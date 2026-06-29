from __future__ import annotations

import html as _html
import re
from typing import Any, Dict, Optional, Set, Union
from urllib.parse import urljoin

from apify import Actor
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from src.taxonomy import (
    extract_taxonomy_maps,
    extract_taxonomy_maps_from_json,
    try_parse_json,
)
from src.modes.generic_cards import extract_generic_cards
from src.modes.generic_directory import extract_generic_directory_page
from src.modes.detail_page_enrichment import enrich_detail_page
from src.modes.confidence import (
    calculate_confidence,
    confidence_level,
)
from src.modes.profile_matching import match_profile_url
from src.adapters.router import get_adapter
from src.enrichment.website_enricher import WebsiteEnricher

FieldSpec = Union[str, Dict[str, Any]]

# -------------------------
# Small helpers / constants
# -------------------------
website_enricher = WebsiteEnricher()
_RPC_RE = re.compile(r"\brpc\d+\b", re.I)
_RSS_RE = re.compile(r"\brss\d+\b", re.I)
_SS_RE = re.compile(r"\bss\d+\b", re.I)  # some pages show ss1
def detect_directory_architecture(html: str, url: str = "") -> str:
    h = (html or "").lower()
    u = (url or "").lower()

    if (
        "growthzoneapp.com" in h
        or "growthzoneapp.com" in u
        or "gzcontent/publicwidgets" in h
        or "publicwidgets/partners.js" in h
        or "/public/js/mmp/" in h
        or "/public/css/mmp/" in h
    ):
        return "growthzone"

    if "custom_listings_lib.js" in h or "simpleview" in h:
        return "simpleview"

    if "resourcedirectoryrwd.js" in h or "enhancedbusinessdirectory" in h:
        return "civicplus"

    if (
        "chambermaster" in h
        or "content/bundles/mni" in h
        or ("business." in u and "/list" in u)
    ):
        return "chambermaster"

    if (
        "wildapricot" in h
        or "wildapricot" in u
        or "powered by wild apricot" in h
    ):
        return "wildapricot"

    if "wix-thunderbolt" in h or "static.parastorage.com" in h:
        return "wix"

    return "unknown"

import json
from typing import Callable, Awaitable

def _lower_keys(m: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in (m or {}).items():
        kk = str(k).strip().lower()
        vv = str(v).strip()
        if kk and vv:
            out[kk] = vv
    return out


async def _safe_goto(page, url: str, timeout_ms: int = 90000) -> None:
    """
    networkidle is unreliable on JS-heavy pages (like /map/).
    Use domcontentloaded as primary, then fallback to load.
    """
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        return
    except PlaywrightTimeoutError:
        await page.goto(url, wait_until="load", timeout=timeout_ms)


async def _wait_for_embedded_data(page, anchor_key: str, timeout_ms: int = 45000) -> None:
    """
    Wait until the JS-injected embedded objects / taxonomy are present in the DOM.
    Without this, page.content() is often too early and taxonomy maps stay empty.
    """
    markers = [
        anchor_key,        # e.g. "logoMedium"
        "pageURL",
        "logoMedium",
        "rpc",             # codes
        "rss",
        '"categories"',
        '"services"',
    ]

    # first, a small delay helps for sites that paint after domcontentloaded
    try:
        await page.wait_for_timeout(1500)
    except Exception:
        pass

    try:
        await page.wait_for_function(
            """(markers) => {
                const html = document.documentElement?.innerHTML || "";
                return markers.some(m => html.includes(m));
            }""",
            markers,
            timeout=timeout_ms,
        )
    except Exception:
        # Don't fail the whole run if the wait times out.
        # We'll still try to extract what we can.
        return


def _unescape(v: Any) -> Any:
    if isinstance(v, str):
        return _html.unescape(v).strip()
    return v


def _normalize_url(base_url: str, maybe_relative: Optional[str]) -> Optional[str]:
    if not maybe_relative:
        return None
    return urljoin(base_url, maybe_relative)


def _is_empty(v: Any) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == "")

def _split_products_into_category_and_services(products: Any) -> tuple[list[str], list[str]]:
    """
    Regeneration Canada stores product/category and regenerative practice text
    inside the `products` field.

    Before 'REGENERATIVE PRACTICES' = product/category information.
    After 'REGENERATIVE PRACTICES' = service/practice information.
    """
    if not products:
        return [], []

    text = _html.unescape(str(products)).strip()
    if not text:
        return [], []

    markers = ["REGENERATIVE PRACTICES", "OBSERVATIONS"]
    upper = text.upper()

    product_part = text
    practice_part = ""

    if "REGENERATIVE PRACTICES" in upper:
        idx = upper.find("REGENERATIVE PRACTICES")
        product_part = text[:idx]
        practice_part = text[idx:].replace("REGENERATIVE PRACTICES", "").strip()

    if "OBSERVATIONS" in practice_part.upper():
        idx = practice_part.upper().find("OBSERVATIONS")
        practice_part = practice_part[:idx]

    def clean_parts(value: str) -> list[str]:
        parts = []
        for x in value.split(";"):
            x = " ".join(x.split()).strip(" .:-")
            if x:
                parts.append(x)

        seen = set()
        out = []
        for x in parts:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    return clean_parts(product_part), clean_parts(practice_part)
async def _scroll_to_load_more(page, scroll_delay_ms: int = 800, max_scrolls: int = 30) -> None:
    last_height = await page.evaluate("document.body.scrollHeight")
    for _ in range(max_scrolls):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(scroll_delay_ms)
        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


# -------------------------
# DOM extraction
# -------------------------

async def _extract_field(card, base_url: str, spec: FieldSpec) -> Optional[str]:
    if isinstance(spec, str):
        selector = spec.strip()
        if selector == ":scope":
            return ((await card.text_content()) or "").strip()

        el = await card.query_selector(selector)
        if not el:
            return None
        return ((await el.text_content()) or "").strip()

    selector = (spec.get("selector") or "").strip()
    attr = spec.get("attr")
    absolute = bool(spec.get("absolute", False))
    closest_link = bool(spec.get("closestLink", False))

    if closest_link:
        try:
            handle = await card.evaluate_handle("node => node.closest('a')")
            if not handle:
                return None
            val = await handle.get_attribute(attr or "href")
            if not val:
                return None
            return _normalize_url(base_url, val) if absolute else val
        except Exception:
            return None

    el = await card.query_selector(selector) if selector else None
    if not el:
        return None

    if attr:
        val = await el.get_attribute(attr)
        if not val:
            return None
        return _normalize_url(base_url, val) if absolute else val

    return ((await el.text_content()) or "").strip()


# -------------------------
# Embedded JS extraction
# -------------------------

def _extract_fields_from_js_object(js_obj: str, keys: list[str]) -> dict:
    out: dict = {}

    for k in keys:
        # 1) String value: key: "value"
        m = re.search(r"\b" + re.escape(k) + r'\s*:\s*"([^"]*)"', js_obj)
        if m:
            out[k] = _html.unescape(m.group(1)).strip()
            continue

        # 2) Array value: key: ["a","b"] or key: [ ... ]
        m = re.search(r"\b" + re.escape(k) + r"\s*:\s*\[([^\]]*)\]", js_obj, re.S)
        if m:
            raw = m.group(1)
            values = re.findall(r'"([^"]+)"', raw)
            if values:
                out[k] = "; ".join(_html.unescape(v).strip() for v in values if v.strip())
            else:
                out[k] = raw.strip()
            continue

        # 3) Object value: key: { ... }
        m = re.search(r"\b" + re.escape(k) + r"\s*:\s*\{([^{}]*)\}", js_obj, re.S)
        if m:
            raw = m.group(1)
            values = re.findall(r'"([^"]+)"', raw)
            if values:
                out[k] = "; ".join(_html.unescape(v).strip() for v in values if v.strip())
            else:
                out[k] = raw.strip()
            continue

        out[k] = None

    return out

def _extract_embedded_objects(html: str, anchor_key: str, keys: Optional[list[str]] = None) -> list[dict]:
    """
    Extract embedded listing objects from JavaScript/HTML.

    The old version captured only a small {...logoMedium...} object.
    Some fields such as products/services/results may be outside that small object,
    so this version extracts a wider window around each listing.
    """
    if not keys:
        keys = [
            "name", "loc", "address", "lat", "lng", "email", "tel",
            "website", "pageURL", "categories", "products", "services",
            "buy", "size", "results", "quote", "logo", "logoMedium"
        ]

    objects = []
    seen = set()

    for m in re.finditer(re.escape(anchor_key), html):
        start = max(0, m.start() - 8000)
        end = min(len(html), m.end() + 8000)
        window = html[start:end]

        obj = _extract_fields_from_js_object(window, keys)

        key = obj.get("pageURL") or obj.get("website") or obj.get("name") or obj.get("logoMedium")
        if not key:
            continue

        if key in seen:
            continue

        seen.add(key)
        objects.append(obj)

    return objects
# -------------------------
# Taxonomy code helpers
# -------------------------

def _extract_codes_any(v: Any, kind: str) -> list[str]:
    if v is None:
        return []
    if isinstance(v, list):
        s = " ".join(str(x) for x in v)
    else:
        s = str(v)

    s = _html.unescape(s).lower()

    if kind == "rpc":
        return [c.lower() for c in _RPC_RE.findall(s)]

    rss = [c.lower() for c in _RSS_RE.findall(s)]
    ss = ["rss" + c[2:] for c in _SS_RE.findall(s)]  # ss12 -> rss12

    out: list[str] = []
    seen: set[str] = set()
    for c in rss + ss:
        if re.fullmatch(r"rss\d+", c) and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _map_codes(codes: list[str], mapping: dict[str, str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()

    for raw in (codes or []):
        c = (raw or "").strip().lower()
        if not c:
            continue

        # only accept valid forms
        if not re.fullmatch(r"(rpc|rss)\d+", c, re.I):
            continue

        lab = mapping.get(c)
        val = _unescape(lab) if lab else c

        if val and val not in seen:
            seen.add(val)
            out.append(val)

    return out


async def _discover_taxonomy_via_endpoints(page, source_url: str, html: str, debug: bool = False) -> tuple[dict, dict]:
    auto_cat: dict = {}
    auto_srv: dict = {}

    candidates: list[str] = []
    seen: Set[str] = set()

    def add(u: str) -> None:
        u = (u or "").strip()
        if not u:
            return
        if u in seen:
            return
        seen.add(u)
        candidates.append(u)

    for m in re.finditer(r'(?:src|href)=["\']([^"\']+)["\']', html, re.I):
        u = (m.group(1) or "").strip()
        if not u:
            continue
        abs_u = urljoin(source_url, u)
        if any(x in abs_u for x in ["wp-json", "admin-ajax", "/api/", ".json"]):
            add(abs_u)

    base = source_url.rstrip("/")
    add(urljoin(base + "/", "wp-json/"))
    add(urljoin(base + "/", "wp-json/wp/v2/"))
    add(urljoin(base + "/", "wp-json/wp/v2/categories"))
    add(urljoin(base + "/", "wp-json/wp/v2/tags"))
    add(urljoin(base + "/", "wp-admin/admin-ajax.php"))

    for u in candidates[:20]:
        try:
            resp = await page.request.get(u, timeout=15000)
            if not resp.ok:
                continue
            txt = await resp.text()
            js = try_parse_json(txt)
            if js is None:
                continue

            c2, s2 = extract_taxonomy_maps_from_json(js)
            if c2:
                auto_cat.update(c2)
            if s2:
                auto_srv.update(s2)

            if debug and (c2 or s2):
                print("DEBUG taxonomy endpoint hit:", u, "cats:", len(c2), "srvs:", len(s2))

            if len(auto_cat) >= 10 or len(auto_srv) >= 10:
                break
        except Exception as e:
            if debug:
                print("DEBUG taxonomy endpoint error:", u, repr(e))
            continue

    return auto_cat, auto_srv


# -------------------------
# Main crawler
# -------------------------

async def run_crawler(
    input_data: Dict[str, Any],
    enable_website_enrichment: bool = False,
    website_timeout_ms: int = 15000,
) -> Dict[str, Any]:

    mode = (input_data.get("mode") or "dom").strip()

    start_urls = input_data.get("startUrls") or []
    max_listings = int(input_data.get("maxListings", 200))
    max_pages = int(input_data.get("maxPages", 50))
    debug = bool(input_data.get("debug", False))

    enable_profile_enrichment = bool(
        input_data.get("enableProfileEnrichment", True)
    )

    max_profile_pages = int(
        input_data.get("maxProfilePages", 5)
    )

    confidence_threshold = int(
        input_data.get("confidenceThreshold", 0)
    )

    if debug:
        print(
            "CONFIG:",
            enable_profile_enrichment,
            max_profile_pages,
            confidence_threshold,
        )

    listing_selector = input_data.get("listingSelector")
    fields: Dict[str, FieldSpec] = input_data.get("fields") or {}

    page_discovery = input_data.get("pageDiscovery", {}) or {}
    pagination_mode = page_discovery.get("mode", "pagination")
    next_page_selector = page_discovery.get("nextPageSelector", "a.next, button[aria-label='Next']")

    infinite_scroll = input_data.get("infiniteScroll", {}) or {}
    infinite_enabled = bool(infinite_scroll.get("enabled", False))
    scroll_delay_ms = int(infinite_scroll.get("scrollDelayMs", 800))
    max_scrolls = int(infinite_scroll.get("maxScrolls", 30))

    embedded = input_data.get("embedded", {}) or {}
    anchor_key = (embedded.get("anchorKey") or "logoMedium").strip()
    keys_to_extract = embedded.get("keys") or None
    field_map: Dict[str, str] = embedded.get("fieldMap") or {}

    if not start_urls:
        raise ValueError("Input must include startUrls.")
    if mode == "dom":
        if not listing_selector:
            raise ValueError("DOM mode: Input must include listingSelector.")
        if not isinstance(fields, dict) or not fields:
            raise ValueError("DOM mode: Input must include fields mapping.")

    elif mode == "embedded_js":
        pass

    elif mode == "generic_cards":
        pass

    elif mode == "generic_directory":
        pass

    elif mode == "auto":
        pass

    else:
        raise ValueError(
            "mode must be 'auto', 'dom', 'embedded_js', 'generic_cards', or 'generic_directory'"
        )

    # ✅ MUST be defined before Playwright + while-loop
    to_visit = [u["url"] if isinstance(u, dict) else str(u) for u in start_urls]


    # ✅ MUST be defined before Playwright + while-loop

    visited: Set[str] = set()
    seen_keys: Set[str] = set()
    pushed = 0

    # ✅ taxonomy maps (mutable dicts => no nonlocal needed)
    all_cat: dict[str, str] = {}
    all_srv: dict[str, str] = {}

    TAX_MAX_BYTES = int(input_data.get("taxonomyMaxBytes", 2_000_000))

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--no-sandbox"],
        )
        page = await browser.new_page()
        page.set_default_timeout(90000)
        page.set_default_navigation_timeout(90000)

        async def _ingest_text_for_taxonomy(text: str) -> None:
            if not text:
                return
            low = text.lower()
            if ("rpc" not in low) and ("rss" not in low) and ("ss" not in low):
                return

            obj = try_parse_json(text)
            if obj is not None:
                c, s = extract_taxonomy_maps_from_json(obj)
                all_cat.update(_lower_keys(c))
                all_srv.update(_lower_keys(s))
                return

            c, s = extract_taxonomy_maps(text)
            all_cat.update(_lower_keys(c))
            all_srv.update(_lower_keys(s))

        async def on_response(resp) -> None:
            try:
                ct = (resp.headers.get("content-type") or "").lower()
                url2 = (resp.url or "").lower()

                if "token.awswaf.com" in url2:
                    all_cat["_blocked"] = "aws_waf"
                    return

                if "cdn-cgi/challenge-platform" in url2:
                    all_cat["_blocked"] = "cloudflare"
                    return

                if "recaptcha" in url2:
                    all_cat["_blocked"] = "recaptcha"

                if any(
                        x in url2
                        for x in (
                                ".png",
                                ".jpg",
                                ".jpeg",
                                ".webp",
                                ".svg",
                                ".css",
                                ".woff",
                                ".woff2",
                                ".ico",
                                ".map",
                        )
                ):
                    return

                if resp.status in (301, 302, 303, 307, 308, 204, 304):
                    return

                interesting_url = any(
                    x in url2
                    for x in (
                        "rpc",
                        "rss",
                        "category",
                        "service",
                        "taxonomy",
                        "member",
                        "directory",
                        "list",
                        "api",
                        "json",
                    )
                )

                interesting_ct = any(
                    x in ct
                    for x in (
                        "json",
                        "javascript",
                        "text",
                        "html",
                        "xml",
                    )
                )

                if not interesting_url and not interesting_ct:
                    return

                try:
                    body = await resp.body()
                except Exception as e:
                    msg = repr(e)

                    if (
                            "No data found for resource" in msg
                            or "Target page, context or browser has been closed" in msg
                            or "TargetClosedError" in msg
                    ):
                        return

                    if debug:
                        print("on_response body error:", msg)

                    return

                if not body or len(body) > TAX_MAX_BYTES:
                    return

                text = body.decode("utf-8", errors="ignore")

                if debug:
                    tlow = text.lower()
                    if ("rpc" in tlow) or ("rss" in tlow) or ("ss" in tlow):
                        print(
                            "✅ HIT taxonomy-ish payload:",
                            resp.status,
                            resp.url,
                            "bytes=",
                            len(body),
                            "ct=",
                            ct,
                        )

                await _ingest_text_for_taxonomy(text)

            except Exception as e:
                if debug:
                    print("on_response error:", repr(e))
                return

        # ✅ attach ONCE
        page.on("response", on_response)

        while to_visit and len(visited) < max_pages and pushed < max_listings:
            url = to_visit.pop(0)
            if url in visited:
                continue
            visited.add(url)

            try:
                await _safe_goto(page, url)

                # tiny buffer so XHRs arrive
                await page.wait_for_timeout(500)

                if debug:
                    print("DEBUG after goto:", url, "taxonomy so far:", len(all_cat), len(all_srv))

            except Exception as e:
                if debug:
                    print("WARNING: could not open page:", url, repr(e))
                continue

            if infinite_enabled:
                await _scroll_to_load_more(page, scroll_delay_ms, max_scrolls)


            # -------------------------
            # GENERIC DIRECTORY MODE
            # -------------------------

            if mode in {"generic_directory", "auto"}:

                html = await page.content()

                architecture = detect_directory_architecture(html, page.url)

                if debug:
                    print(f"DEBUG architecture detected: {architecture}")

                if architecture != "unknown":
                    adapter = get_adapter(
                        architecture=architecture,
                        source_url=page.url,
                        debug=debug,
                    )
                    if debug:
                        print("DEBUG adapter:", adapter)
                        print("DEBUG mode:", mode)
                        print("DEBUG architecture:", architecture)

                    if mode == "auto" and adapter:
                        adapter_records = await adapter.crawl(
                            page,
                            max_records=max_listings,
                        )

                        if debug:
                            print("DEBUG adapter records:", len(adapter_records))

                        for record in adapter_records[:max_listings]:

                            if enable_website_enrichment and record.get("website"):
                                record = await website_enricher.enrich_record_from_website(
                                    page,
                                    record,
                                    timeout_ms=website_timeout_ms,
                                )

                            await Actor.push_data(record)
                            pushed += 1

                        return {
                            "status": "adapter_extraction_complete",
                            "architecture": architecture,
                            "records_found": len(adapter_records),
                            "crawl_mode": "auto",
                            "recommended_strategy": f"{architecture}_adapter",
                        }

                    await Actor.push_data({
                        "source_url": page.url,
                        "status": "architecture_detected",
                        "architecture": architecture,
                        "records_found": 0,
                        "crawl_mode": mode,
                        "recommended_strategy": f"{architecture}_adapter",
                        "note": "Known directory platform detected. Dedicated adapter recommended."
                    })

                    return {
                        "status": "architecture_detected",
                        "architecture": architecture,
                        "records_found": 0,
                        "crawl_mode": mode,
                        "recommended_strategy": f"{architecture}_adapter",
                    }

                await Actor.set_value(
                    "DEBUG_PAGE.html",
                    html,
                    content_type="text/html",
                )

                result = extract_generic_directory_page(
                    html=html,
                    source_url=url,
                )
                if all_cat.get("_blocked"):
                    reason_map = {
                        "aws_waf": "AWS WAF",
                        "cloudflare": "Cloudflare Challenge",
                        "recaptcha": "reCAPTCHA",
                    }

                    await Actor.push_data({
                        "source_url": url,
                        "status": "blocked",
                        "blocked_reason": reason_map.get(all_cat.get("_blocked"), all_cat.get("_blocked")),
                        "records_found": 0,
                        "crawl_mode": mode,
                    })

                    continue

                if all_cat.get("_blocked"):
                    result["stats"]["blocked"] = True

                if debug:
                    print(f"DEBUG generic_directory stats: {result.get('stats')}")
                    print(f"DEBUG generic_directory selectors: {result.get('selectors')[:3]}")
                    print(f"DEBUG profile links found: {len(result.get('profile_links', []))}")

                if result.get("stats", {}).get("blocked"):
                    continue

                # Push records found directly on directory page
                records = result.get("records", [])
                profile_links = result.get(
                    "profile_links",
                    []
                )[:max_profile_pages]

                used_profiles = set()

                for idx, record in enumerate(records):
                    if pushed >= max_listings:
                        break

                    profile_url = match_profile_url(
                        record,
                        profile_links,
                    )

                    if not profile_url and idx < len(profile_links):
                        profile_url = profile_links[idx]

                    merged = {
                        "entity_name": record.get("name"),
                        "website": record.get("website"),
                        "email": record.get("email"),
                        "phone": record.get("phone"),
                        "source_url": record.get("source_url"),
                        "services": record.get("description"),
                        "social_links": record.get("social_links"),
                        "profile_url": profile_url,
                        "blocked": False,
                    }

                    if (
                            enable_profile_enrichment
                            and profile_url
                            and profile_url not in used_profiles
                    ):
                        try:
                            await page.goto(
                                profile_url,
                                wait_until="domcontentloaded",
                                timeout=30000,
                            )

                            detail_html = await page.content()
                            enrichment = enrich_detail_page(detail_html)
                            socials = enrichment.get("socials", {}) or {}

                            merged["website"] = merged.get("website") or enrichment.get("website", "")
                            merged["email"] = merged.get("email") or enrichment.get("email", "")
                            merged["phone"] = merged.get("phone") or enrichment.get("phone", "")

                            merged["linkedin"] = enrichment.get("linkedin") or socials.get("linkedin", "")
                            merged["facebook"] = enrichment.get("facebook") or socials.get("facebook", "")
                            merged["instagram"] = enrichment.get("instagram") or socials.get("instagram", "")
                            merged["youtube"] = enrichment.get("youtube") or socials.get("youtube", "")
                            merged["twitter"] = enrichment.get("twitter") or socials.get("twitter", "")

                            used_profiles.add(profile_url)

                        except Exception as e:
                            if debug:
                                print("DETAIL PAGE ERROR:", profile_url, repr(e))

                    merged["confidence_score"] = calculate_confidence(merged)
                    merged["confidence_level"] = confidence_level(
                        merged["confidence_score"]
                    )

                    if merged["confidence_score"] < confidence_threshold:
                        continue

                    key = (
                            merged.get("website")
                            or merged.get("email")
                            or merged.get("phone")
                            or merged.get("entity_name")
                            or merged.get("profile_url")
                    )

                    if key in seen_keys:
                        continue

                    seen_keys.add(key)
                    await Actor.push_data(merged)
                    pushed += 1

                continue
            # -------------------------
            # GENERIC CARDS MODE
            # -------------------------

            if mode == "generic_cards":

                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=15000)
                    await page.wait_for_timeout(2000)
                    html = await page.content()

                    architecture = detect_directory_architecture(html, page.url)

                    if debug:
                        print(f"DEBUG architecture detected: {architecture}")

                        if architecture != "unknown":
                            await Actor.push_data(
                                {
                                    "source_url": page.url,
                                    "status": "architecture_detected",
                                    "architecture": architecture,
                                    "records_found": 0,
                                    "crawl_mode": mode,
                                    "note": "Known directory platform detected. Dedicated adapter recommended."
                                }
                            )
                            return {
                                "status": "architecture_detected",
                                "architecture": architecture,
                                "records_found": 0,
                                "crawl_mode": mode,
                            }

                        await Actor.push_data(
                            {
                                "source_url": page.url,
                                "status": "architecture_detected",
                                "architecture": architecture,
                                "crawl_mode": mode,
                                "records_found": 0,
                            }
                        )

                        if architecture in {
                            "simpleview",
                            "civicplus",
                            "chambermaster",
                            "growthzone",
                            "wildapricot",
                            "wix",
                        }:

                            return {
                                "status": "architecture_detected",
                                "architecture": architecture,
                                "records_found": 0,
                                "crawl_mode": mode,
                            }

                except Exception as e:
                    if debug:
                        print("WARNING: could not capture page HTML:", url, repr(e))
                    continue

                records = extract_generic_cards(
                    html=html,
                    source_url=url,
                )

                if debug:
                    print(
                        f"DEBUG generic_cards: extracted {len(records)} records"
                    )

                for record in records:

                    if pushed >= max_listings:
                        break

                    key = (
                            record.get("website")
                            or record.get("email")
                            or record.get("name")
                    )

                    if key in seen_keys:
                        continue

                    seen_keys.add(key)

                    await Actor.push_data({
                        "entity_name": record.get("name"),
                        "website": record.get("website"),
                        "email": record.get("email"),
                        "phone": record.get("phone"),
                        "source_url": record.get("source_url"),
                        "services": record.get("description"),
                        "social_links": record.get("social_links"),
                    })

                    pushed += 1

                continue
            # ---------- EMBEDDED JS MODE ----------
            if mode == "embedded_js":
                await _wait_for_embedded_data(page, anchor_key=anchor_key, timeout_ms=45000)
                await page.wait_for_timeout(1500)

                html = await page.content()

                # Inline extraction (sometimes works)
                auto_cat, auto_srv = extract_taxonomy_maps(html)
                all_cat.update(_lower_keys(auto_cat))
                all_srv.update(_lower_keys(auto_srv))

                # Endpoint fallback (optional)
                if (not all_cat) and (not all_srv):
                    e_cat, e_srv = await _discover_taxonomy_via_endpoints(page, url, html, debug=debug)
                    all_cat.update(_lower_keys(e_cat))
                    all_srv.update(_lower_keys(e_srv))

                if debug:
                    print("DEBUG taxonomy (global): categories =", len(all_cat), "services =", len(all_srv))

                objs = _extract_embedded_objects(html, anchor_key=anchor_key, keys=keys_to_extract)
                if debug:
                    print("DEBUG embedded_js: objs_len =", len(objs))

                for i, obj in enumerate(objs):
                    if pushed >= max_listings:
                        break

                    record: Dict[str, Any] = {"source_url": url}

                    if field_map:
                        for src_key, out_key in field_map.items():
                            record[out_key] = obj.get(src_key)
                    else:
                        record.update(obj)

                    for k in ["entity_name", "location", "address", "quote", "website", "profile_url"]:
                        if k in record:
                            record[k] = _unescape(record.get(k))

                    key = (
                        record.get("profile_url")
                        or record.get("website")
                        or record.get("logo_medium")
                        or record.get("logoMedium")
                        or record.get("logo")
                        or f"{url}#{i}"
                    )
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)

                    if all(_is_empty(record.get(k)) for k in record.keys() if k != "source_url"):
                        continue

                    def _fallback_list(*values):
                        out = []
                        for value in values:
                            if not value:
                                continue

                            if isinstance(value, list):
                                for x in value:
                                    if x:
                                        out.append(str(x).strip())
                            elif isinstance(value, dict):
                                for x in value.values():
                                    if x:
                                        out.append(str(x).strip())
                            else:
                                s = str(value).strip()
                                if s:
                                    out.append(s)

                        # remove duplicates
                        seen = set()
                        clean = []
                        for x in out:
                            if x and x not in seen:
                                seen.add(x)
                                clean.append(x)

                        return clean

                    cat_codes = _extract_codes_any(record.get("categories"), kind="rpc")
                    srv_codes = _extract_codes_any(record.get("services"), kind="rss")

                    record["category_codes"] = cat_codes
                    record["service_codes"] = srv_codes

                    record["category_names"] = _map_codes(cat_codes, all_cat)
                    record["service_names"] = _map_codes(srv_codes, all_srv)

                    # Regeneration Canada fallback:
                    # products contains both product/category info and regenerative practices.
                    product_categories, regenerative_services = _split_products_into_category_and_services(
                        record.get("products")
                    )

                    if not record["category_names"] and product_categories:
                        record["category_names"] = product_categories

                    if not record["service_names"] and regenerative_services:
                        record["service_names"] = regenerative_services

                    record["category_names_str"] = "; ".join(record["category_names"]) if record[
                        "category_names"] else ""
                    record["service_names_str"] = "; ".join(record["service_names"]) if record["service_names"] else ""
                    # Strong fallback: use products/categories when decoded taxonomy is empty
                    if not record["category_names"]:
                        record["category_names"] = _fallback_list(
                            record.get("products"),
                            record.get("category"),
                            record.get("categories"),
                        )

                    # Strong fallback: use services/how_to_buy when decoded taxonomy is empty
                    if not record["service_names"]:
                        record["service_names"] = _fallback_list(
                            record.get("services"),
                            record.get("service"),
                            record.get("how_to_buy"),
                        )

                    record["category_names_str"] = "; ".join(record["category_names"]) if record[
                        "category_names"] else ""
                    record["service_names_str"] = "; ".join(record["service_names"]) if record["service_names"] else ""


                    await Actor.push_data(record)
                    pushed += 1

                continue

            # ---------- DOM MODE ----------
            cards = await page.query_selector_all(listing_selector)
            for i, card in enumerate(cards):
                if pushed >= max_listings:
                    break

                record: Dict[str, Any] = {"source_url": url}

                for field_name, spec in fields.items():
                    try:
                        record[field_name] = await _extract_field(card, url, spec)
                    except Exception:
                        record[field_name] = None

                if all(_is_empty(record.get(k)) for k in record.keys() if k != "source_url"):
                    continue
                if "entity_name" in record and _is_empty(record.get("entity_name")):
                    continue

                key = record.get("profile_url") or record.get("website") or record.get("entity_name") or f"{url}#{i}"
                if key in seen_keys:
                    continue
                seen_keys.add(key)

                if record.get("products"):
                    product_categories, regenerative_services = _split_products_into_category_and_services(
                        record.get("products"))
                    record["category_names_str"] = "; ".join(product_categories)
                    record["service_names_str"] = "; ".join(regenerative_services)

                await Actor.push_data(record)
                pushed += 1

            if pagination_mode == "pagination" and pushed < max_listings:
                try:
                    next_el = await page.query_selector(next_page_selector)
                    if next_el:
                        href = await next_el.get_attribute("href")
                        if href:
                            next_url = _normalize_url(url, href)
                            if next_url and next_url not in visited:
                                to_visit.append(next_url)
                        else:
                            await next_el.click()
                            await page.wait_for_timeout(800)
                            next_url = page.url
                            if next_url and next_url not in visited and next_url != url:
                                to_visit.append(next_url)
                except Exception:
                    pass

        await browser.close()

    await Actor.set_value(
        "STATS",
        {"pushed": pushed, "visited_pages": len(visited), "unique_keys": len(seen_keys), "mode": mode},
    )

    # ---- Monetization: charge per validated business record ----
    if pushed > 0:
        try:
            await Actor.charge(
                event_name="business_result",
                count=pushed,
            )
            Actor.log.info(f"Charged business_result event for {pushed} business records.")
        except Exception as e:
            Actor.log.warning(f"Could not charge business_result event: {e}")

    return {"category_map": all_cat, "service_map": all_srv}
