from __future__ import annotations

import html
import io
import csv
import json
from typing import Any, Dict

from apify import Actor

from src.crawler import run_crawler
from src.taxonomy_static import RPC_CATEGORY_MAP, RSS_SERVICE_MAP
from src.run_summary import print_run_summary

def _clean_label(v: Any) -> str:
    if v is None:
        return ""
    s = html.unescape(str(v))
    return " ".join(s.split()).strip()


def _normalize_tax_map(m: Dict[Any, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in (m or {}).items():
        kk = str(k).strip().lower()
        vv = _clean_label(v)
        if kk and vv:
            out[kk] = vv
    return out


def _cell(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (str, int, float, bool)):
        return str(v)
    if isinstance(v, (list, tuple, set)):
        return "; ".join(str(x) for x in v)
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def _codes_to_names(value: Any, mapping: Dict[Any, Any]) -> str:
    if not value:
        return ""

    normalized_map = _normalize_tax_map(mapping)

    if isinstance(value, str):
        codes = [x.strip().lower() for x in value.replace(",", ";").split(";")]
    elif isinstance(value, (list, tuple, set)):
        codes = [str(x).strip().lower() for x in value]
    else:
        codes = [str(value).strip().lower()]

    names = []
    seen = set()

    for code in codes:
        if not code:
            continue

        name = normalized_map.get(code, code)

        if name and name not in seen:
            seen.add(name)
            names.append(name)

    return "; ".join(names)


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        value = "; ".join(str(x) for x in value if x)
    elif isinstance(value, dict):
        value = "; ".join(str(x) for x in value.values() if x)
    else:
        value = str(value)

    value = html.unescape(value)
    return " ".join(value.split()).strip()


def _clean_semicolon(value: Any) -> str:
    value = _clean_text(value)
    if not value:
        return ""

    parts = []
    seen = set()

    for part in value.split(";"):
        p = " ".join(part.split()).strip(" .:-")
        if not p:
            continue
        if p.upper() in {"REGENERATIVE PRACTICES", "OBSERVATIONS"}:
            continue
        if p not in seen:
            seen.add(p)
            parts.append(p)

    return "; ".join(parts)


def _split_source_text(value: Any) -> tuple[str, str]:
    text = _clean_text(value)
    if not text:
        return "", ""

    upper = text.upper()
    category_part = text
    service_part = ""

    if "REGENERATIVE PRACTICES" in upper:
        idx = upper.find("REGENERATIVE PRACTICES")
        category_part = text[:idx]
        service_part = text[idx + len("REGENERATIVE PRACTICES"):]

    if "OBSERVATIONS" in service_part.upper():
        idx = service_part.upper().find("OBSERVATIONS")
        service_part = service_part[:idx]

    return _clean_semicolon(category_part), _clean_semicolon(service_part)


async def export_dataset_to_kv(
    out_base: str,
    write_csv: bool,
    write_xlsx: bool,
    columns_mode: str = "default",
) -> None:
    ds = await Actor.open_dataset()
    data = await ds.get_data(limit=999999)
    items = data.items or []

    items = [r for r in items if not (isinstance(r, dict) and r.get("_probe"))]

    rows_with_products = 0
    rows_with_results = 0
    rows_with_quote = 0
    filled_categories = 0
    filled_services = 0

    for r in items:
        if not isinstance(r, dict):
            continue
        # ------------------------------------------------------------------
        # Standard export metadata
        # ------------------------------------------------------------------
        r.setdefault("status", "success")
        r.setdefault("blocked_reason", "")
        r.setdefault("records_found", len(items))

        if r.get("category_codes"):
            r["category_names_str"] = _codes_to_names(
                r.get("category_codes"),
                RPC_CATEGORY_MAP,
            )

        if r.get("service_codes"):
            r["service_names_str"] = _codes_to_names(
                r.get("service_codes"),
                RSS_SERVICE_MAP,
            )

        if _clean_text(r.get("products")):
            rows_with_products += 1
        if _clean_text(r.get("results")):
            rows_with_results += 1
        if _clean_text(r.get("quote")):
            rows_with_quote += 1

        source_text = (
            _clean_text(r.get("products"))
            or _clean_text(r.get("results"))
            or _clean_text(r.get("quote"))
            or _clean_text(r.get("categories"))
            or _clean_text(r.get("services"))
        )

        category_text, service_text = _split_source_text(source_text)

        if not _clean_text(r.get("category_names_str")) and category_text:
            r["category_names_str"] = category_text
            filled_categories += 1

        if not _clean_text(r.get("service_names_str")) and service_text:
            r["service_names_str"] = service_text
            filled_services += 1



    Actor.log.info(f"EXPORT: dataset items={len(items)}")
    if items:
        sample = next(
            (
                r for r in items
                if r.get("products") or r.get("category_names_str") or r.get("service_names_str")
            ),
            items[0],
        )


        Actor.log.info(f"EXPORT: dataset items={len(items)}")

    DEFAULT_COLUMNS = [
        "entity_name",
        "website",
        "email",
        "phone",
        "fax",

        "linkedin",
        "facebook",
        "instagram",
        "youtube",
        "twitter",

        "location",
        "address",
        "city",
        "state",
        "postal_code",

        "description",
        "hours",
        "driving_directions",

        "profile_url",
        "confidence_score",
        "source_url",
        "status",
        "blocked_reason",
        "records_found",
        "crawl_mode",

        "website_enrichment_status",
        "website_enrichment_error",
    ]

    ALL_COLUMNS = [
        *DEFAULT_COLUMNS,
        "category_codes",
        "service_codes",
        "category_names",
        "service_names",
        "logo",
        "logo_medium",
        "lat",
        "lng",
        "quote",
        "services",
        "how_to_buy",
        "size",
        "results",
    ]

    cols = ALL_COLUMNS if (columns_mode or "").strip().lower() == "all" else DEFAULT_COLUMNS

    if write_csv:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(cols)
        for row in items:
            w.writerow([_cell(row.get(c)) for c in cols])

        await Actor.set_value(
            f"{out_base}.csv",
            buf.getvalue().encode("utf-8"),
            content_type="text/csv",
        )
        Actor.log.info(f"Uploaded KV: {out_base}.csv")

    if write_xlsx:
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "data"
        ws.append(cols)

        for row in items:
            ws.append([_cell(row.get(c)) for c in cols])

        xbuf = io.BytesIO()
        wb.save(xbuf)

        await Actor.set_value(
            f"{out_base}.xlsx",
            xbuf.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        Actor.log.info(f"Uploaded KV: {out_base}.xlsx")


async def main() -> None:
    async with Actor:
        input_data = await Actor.get_input() or {}

        if not input_data.get("startUrls"):
            su = (input_data.get("startUrl") or "").strip()
            if su:
                input_data["startUrls"] = [{"url": su}]

        if not input_data:
            input_data = {
                "mode": "embedded_js",
                "startUrls": [{"url": "https://regenerationcanada.org/en/map/"}],
                "maxListings": 250,
                "maxPages": 1,
                "embedded": {
                    "enabled": True,
                    "preferJsonLd": True,
                    "anchorKey": "logoMedium",
                    "keys": [
                        "name",
                        "loc",
                        "address",
                        "lat",
                        "lng",
                        "email",
                        "tel",
                        "website",
                        "pageURL",
                        "categories",
                        "products",
                        "services",
                        "buy",
                        "size",
                        "results",
                        "quote",
                        "logo",
                        "logoMedium",
                    ],
                    "fieldMap": {
                        "name": "entity_name",
                        "loc": "location",
                        "address": "address",
                        "lat": "lat",
                        "lng": "lng",
                        "email": "email",
                        "tel": "phone",
                        "website": "website",
                        "pageURL": "profile_url",
                        "categories": "categories",
                        "products": "products",
                        "services": "services",
                        "buy": "how_to_buy",
                        "size": "size",
                        "results": "results",
                        "quote": "quote",
                        "logo": "logo",
                        "logoMedium": "logo_medium",
                    },
                },
                "outputCsv": True,
                "outputXlsx": True,
                "outputColumnsMode": "default",
                "outputBaseName": "directory_listings_demo",
                "taxonomy": {"categoryMap": {}, "serviceMap": {}},
                "debug": False,
            }

        Actor.log.info(f"LOADED INPUT keys={list(input_data.keys())}")

        start_url = (input_data.get("startUrls") or [{}])[0].get("url")

        await Actor.set_value(
            "PROBE.json",
            {"_probe": True, "message": "KV store works", "start_url": start_url},
            content_type="application/json",
        )

        enable_website_enrichment = bool(
            input_data.get("enableWebsiteEnrichment", False)
        )

        website_timeout_ms = int(
            input_data.get("websiteTimeoutMs", 15000)
        )

        crawl_info = await run_crawler(
            input_data,
            enable_website_enrichment=enable_website_enrichment,
            website_timeout_ms=website_timeout_ms,
        ) or {}

        ds = await Actor.open_dataset()
        peek = await ds.get_data(limit=3)
        Actor.log.info(
            f"DATASET AFTER CRAWL count={len(peek.items or [])} "
            f"keys={list((peek.items or [{}])[0].keys()) if (peek.items or []) else []}"
        )

        auto_cat = crawl_info.get("category_map", {}) or {}
        auto_srv = crawl_info.get("service_map", {}) or {}

        taxonomy = input_data.get("taxonomy", {}) or {}
        manual_cat = taxonomy.get("categoryMap", {}) or {}
        manual_srv = taxonomy.get("serviceMap", {}) or {}

        category_map = {
            **_normalize_tax_map(RPC_CATEGORY_MAP),
            **_normalize_tax_map(auto_cat),
            **_normalize_tax_map(manual_cat),
        }
        service_map = {
            **_normalize_tax_map(RSS_SERVICE_MAP),
            **_normalize_tax_map(auto_srv),
            **_normalize_tax_map(manual_srv),
        }

        if input_data.get("debug"):
            Actor.log.info(f"DEBUG category_map sample={list(category_map.items())[:10]}")
            Actor.log.info(f"DEBUG service_map sample={list(service_map.items())[:10]}")

        await Actor.set_value(
            "TAXONOMY.json",
            {
                "source_url": start_url,
                "category_map": category_map,
                "service_map": service_map,
                "counts": {
                    "auto_categories": len(auto_cat),
                    "auto_services": len(auto_srv),
                    "manual_categories": len(manual_cat),
                    "manual_services": len(manual_srv),
                    "final_categories": len(category_map),
                    "final_services": len(service_map),
                },
            },
            content_type="application/json",
        )

        Actor.log.info("Starting dataset export to KV...")

        out_base = input_data.get("outputBaseName", "output")
        write_csv = bool(input_data.get("outputCsv", True))
        write_xlsx = bool(input_data.get("outputXlsx", False))

        await export_dataset_to_kv(
            out_base=out_base,
            write_csv=write_csv,
            write_xlsx=write_xlsx,
            columns_mode=str(input_data.get("outputColumnsMode", "default")),
        )

        ds = await Actor.open_dataset()
        final_data = await ds.get_data(limit=999999)
        final_items = final_data.items or []

        export_paths = {
            "csv": f"{out_base}.csv" if write_csv else "",
            "xlsx": f"{out_base}.xlsx" if write_xlsx else "",
        }

        print_run_summary(
            items=final_items,
            crawl_info=crawl_info,
            export_paths=export_paths,
        )

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

