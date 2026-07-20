from __future__ import annotations

import re

from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from src.adapters.base import BaseDirectoryAdapter
from src.adapters.capabilities import AdapterCapabilities
from src.adapters.models import AdapterInfo
from src.models.business_record import BusinessRecord
# src/adapters/chambermaster.py
from dataclasses import dataclass

@dataclass
class RawMemberProfile:
    name: str = ""

    phone: str = ""
    fax: str = ""

    email: str = ""
    website: str = ""

    facebook: str = ""
    linkedin: str = ""
    instagram: str = ""
    youtube: str = ""
    twitter: str = ""

    address: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""

    description: str = ""
    hours: str = ""
    driving_directions: str = ""

    category_names: str = ""
    profile_url: str = ""

class ChamberMasterParser:
    """Parse ChamberMaster HTML without performing network access."""

    @staticmethod
    def clean_text(value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    def parse_member_profile(
        self,
        html: str,
        *,
        category_names: str = "",
        profile_url: str = "",
    ) -> RawMemberProfile:
        soup = BeautifulSoup(html or "", "html.parser")

        profile = RawMemberProfile(
            category_names=category_names,
            profile_url=profile_url,
        )

        title = soup.select_one(".gz-pagetitle")
        if title:
            profile.name = self.clean_text(
                title.get_text(" ", strip=True)
            )

        phone = soup.select_one(
            ".gz-card-phone span[itemprop='telephone']"
        )
        if phone:
            profile.phone = self.clean_text(
                phone.get_text(" ", strip=True)
            )

        fax = soup.select_one(
            ".gz-card-fax span[itemprop='faxNumber']"
        )
        if fax:
            profile.fax = self.clean_text(
                fax.get_text(" ", strip=True)
            )

        website = soup.select_one(".gz-card-website a[href]")
        if website:
            profile.website = (website.get("href") or "").strip()

        email = soup.select_one(".gz-card-email a[href^='mailto:']")
        if email:
            profile.email = (
                email.get("href", "")
                .replace("mailto:", "", 1)
                .split("?", 1)[0]
                .strip()
            )
        social_selectors = {
            "facebook": "a[href*='facebook.com']",
            "linkedin": "a[href*='linkedin.com']",
            "instagram": "a[href*='instagram.com']",
            "youtube": "a[href*='youtube.com'], a[href*='youtu.be']",
            "twitter": "a[href*='twitter.com'], a[href*='x.com']",
        }

        for field_name, selector in social_selectors.items():
            element = soup.select_one(selector)
            if not element:
                continue

            value = (element.get("href") or "").strip()
            if value:
                setattr(profile, field_name, value)

        return profile

class ChamberMasterAdapter(BaseDirectoryAdapter):
    ##############################################################################
    # Metadata
    ##############################################################################
    architecture = "chambermaster"

    INFO = AdapterInfo(
        key="chambermaster",
        name="ChamberMaster",
        version="1.0",
        author="Adinfosys",
        website="https://www.chambermaster.com/",
        description="Adapter for ChamberMaster-powered chamber of commerce business directories.",
    )

    CAPABILITIES = AdapterCapabilities(
        name="ChamberMaster",
        support_level="fully_supported",
        anti_bot_risk="low",
        notes="Works as a standard supported directory adapter.",

        requires_javascript=True,
        requires_proxy=False,
        requires_residential_proxy=False,
        requires_external_proxy_access=False,

        search=True,
        category_filter=True,
        location_filter=False,
        pagination=True,

        website_links=True,
        social_links=True,
        ratings=False,
        reviews=False,
        contact_details=True,
        business_hours=True,
    )

    BAD_TEXT = {
        "home",
        "login",
        "directory",
        "contact",
        "contact us",
        "join",
        "join now",
        "events",
        "calendar",
        "news",
        "about",
        "advertise",
        "privacy policy",
        "terms",
    }

    ###########################################################################
    # Initialization
    ###########################################################################
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.parser = ChamberMasterParser()

        self.stats = {
            "categories": 0,
            "member_urls": 0,
            "profiles_processed": 0,
            "profiles_failed": 0,
        }

    def _extract_category_name(self, html: str, category_url: str = "") -> str:
        soup = BeautifulSoup(html or "", "html.parser")

        selectors = [
            "h1",
            ".gz-pagetitle",
            ".mn-title",
            ".page-title",
            "title",
        ]

        for selector in selectors:
            el = soup.select_one(selector)
            if el:
                text = self._clean_text(el.get_text(" ", strip=True))
                text = re.sub(r"\s*\|\s*.*$", "", text).strip()
                if text:
                    return text

        return category_url.rstrip("/").split("/")[-1].replace("-", " ").title()

    ###########################################################################
    # Shared helpers
    ###########################################################################
    def _debug(self, *args):
        if self.debug:
            print(*args)

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    def _normalize_member_url(self, url: str) -> str:
        """
        Normalize ChamberMaster member/category URLs before deduplication.
        Removes query strings, fragments, and trailing slashes.
        """
        if not url:
            return ""

        parts = urlsplit(urljoin(self.source_url, url))
        path = parts.path.rstrip("/")

        return urlunsplit(
            (
                parts.scheme.lower(),
                parts.netloc.lower(),
                path,
                "",
                "",
            )
        )
    def _calculate_confidence(self, record: BusinessRecord) -> float:
        """
        Calculate a simple completeness score for CRM/export quality.
        """
        score = 0.0

        if record.entity_name:
            score += 0.30
        if record.phone:
            score += 0.20
        if record.website:
            score += 0.20
        if record.address:
            score += 0.20
        if record.city and record.state:
            score += 0.10

    ###########################################################################
    # Category discovery
    ###########################################################################

    def _extract_category_links(self, html: str) -> list[str]:
        """
        Extract ChamberMaster category/search URLs from a directory landing page.
        """
        soup = BeautifulSoup(html or "", "html.parser")
        categories = set()

        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()

            if not href:
                continue

            href_lower = href.lower()

            if "/list/category/" in href_lower:
                categories.add(urljoin(self.source_url, href))

            elif "/list/search" in href_lower or "/list/searchalpha/" in href_lower:
                categories.add(urljoin(self.source_url, href))

        result = sorted(categories)

        self._debug("DEBUG ChamberMaster categories:", len(result))

        if result:
            self._debug("DEBUG ChamberMaster first categories:", result[:5])

        return result



    def _extract_next_page(self, html: str) -> str | None:
        """
        Extract the next pagination URL from a ChamberMaster category page.

        Query parameters are preserved because ChamberMaster may use them
        to identify the next results page.
        """
        soup = BeautifulSoup(html or "", "html.parser")

        # Prefer explicit pagination metadata.
        rel_next = soup.select_one("a[rel='next'][href]")

        if rel_next:
            href = (rel_next.get("href") or "").strip()

            if href:
                return urljoin(self.source_url, href)

        # Common ChamberMaster and Bootstrap pagination structures.
        pagination_selectors = (
            "li.next a[href]",
            ".pagination-next a[href]",
            ".pager-next a[href]",
            "a.next[href]",
        )

        for selector in pagination_selectors:
            link = soup.select_one(selector)

            if not link:
                continue

            href = (link.get("href") or "").strip()

            if href:
                return urljoin(self.source_url, href)

        # Fallback for links identified by visible text or accessibility metadata.
        for link in soup.select("a[href]"):
            href = (link.get("href") or "").strip()

            if not href:
                continue

            text = self._clean_text(
                link.get_text(" ", strip=True)
            ).lower()

            aria_label = self._clean_text(
                link.get("aria-label") or ""
            ).lower()

            title = self._clean_text(
                link.get("title") or ""
            ).lower()

            classes = {
                str(class_name).strip().lower()
                for class_name in (link.get("class") or [])
                if class_name
            }

            is_next = (
                text in {"next", "next page", "›", "»"}
                or aria_label in {"next", "next page"}
                or title in {"next", "next page"}
                or "next" in classes
            )

            if is_next:
                return urljoin(self.source_url, href)

        return None


        return round(score, 2)

    async def discover_categories(self, page, html: str = "") -> list[str]:
        if not html:
            html = await page.content()

        return self._extract_category_links(html)

    ###########################################################################
    # Member discovery
    ###########################################################################

    def _extract_member_links(self, html: str) -> list[str]:
        """
        Extract ChamberMaster member/profile URLs from a category/search page.
        """
        soup = BeautifulSoup(html or "", "html.parser")
        member_urls = set()

        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()

            if not href:
                continue

            h = href.lower()

            if "/list/member/" in h or "/member/" in h:
                if "newmemberapp" in h:
                    continue

                absolute_url = urljoin(self.source_url, href)
                member_urls.add(self._normalize_member_url(absolute_url))

        return sorted(member_urls)

    async def _discover_member_urls_from_category(
        self,
        page,
        category_url: str,
    ) -> dict[str, set[str]]:
        urls: dict[str, set[str]] = {}
        current_url = category_url
        visited_pages = set()
        category_name = ""

        while current_url:
            current_url = self._normalize_member_url(current_url)

            if current_url in visited_pages:
                break

            visited_pages.add(current_url)

            self._debug("DEBUG ChamberMaster page:", current_url)

            await page.goto(
                current_url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            await page.wait_for_timeout(500)

            html = await page.content()

            if not category_name:
                category_name = self._extract_category_name(html, category_url)

            links = self._extract_member_links(html)

            for link in links:
                urls.setdefault(link, set()).add(category_name)

            self._debug(
                "DEBUG member links:",
                len(links),
                "total:",
                len(urls),
            )

            current_url = self._extract_next_page(html)

        return urls

    async def discover_member_urls(self, page, category_urls: list[str]) -> list[dict[str, Any]]:
        member_map: dict[str, set[str]] = {}

        for i, category_url in enumerate(category_urls, start=1):
            try:
                self._debug(
                    f"DEBUG ChamberMaster category {i}/{len(category_urls)}:",
                    category_url,
                )

                found = await self._discover_member_urls_from_category(
                    page,
                    category_url,
                )

                for member_url, categories in found.items():
                    member_map.setdefault(member_url, set()).update(categories)

                self._debug(
                    "DEBUG ChamberMaster unique member URLs so far:",
                    len(member_map),
                )

            except Exception as e:
                self.stats["profiles_failed"] += 1
                self._debug(
                    "DEBUG ChamberMaster category error:",
                    category_url,
                    repr(e),
                )

        result = [
            {
                "url": member_url,
                "category_names": "; ".join(sorted(categories)),
            }
            for member_url, categories in sorted(member_map.items())
        ]

        self.stats["member_urls"] = len(result)

        return result

    ###########################################################################
    # Profile extraction
    ###########################################################################

    async def extract_member(self, page, member_info) -> dict[str, Any]:
        if isinstance(member_info, dict):
            member_url = member_info.get("url", "")
            category_names = member_info.get("category_names", "")
        else:
            member_url = str(member_info)
            category_names = ""

        if not member_url:
            return {}

        await page.goto(
            member_url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        await page.wait_for_timeout(500)

        html = await page.content()

        profile = self.parser.parse_member_profile(
            html,
            category_names=category_names,
            profile_url=member_url,
        )

        if self.debug:
            debug_dir = Path("debug")
            debug_dir.mkdir(exist_ok=True)

            with open(debug_dir / "member_debug.html", "w", encoding="utf-8") as f:
                f.write(html)
        soup = BeautifulSoup(html or "", "html.parser")

        name = profile.name
        phone = profile.phone
        fax = profile.fax

        website = profile.website

        # ChamberMaster may hide member emails behind a JavaScript contact form.
        # If no mailto link exists, the parser intentionally leaves email empty.
        email = profile.email

        facebook = profile.facebook
        linkedin = profile.linkedin
        instagram = profile.instagram
        youtube = profile.youtube
        twitter = profile.twitter

        for a in soup.select(".gz-card-social a[href]"):
            href = (a.get("href") or "").strip()

            href_lower = href.lower()

            if "facebook.com" in href_lower:
                facebook = href

            elif "linkedin.com" in href_lower:
                linkedin = href

            elif "instagram.com" in href_lower:
                instagram = href

            elif "youtube.com" in href_lower:
                youtube = href

            elif "twitter.com" in href_lower or "x.com" in href_lower:
                twitter = href

        address = profile.address
        city = profile.city
        state = profile.state
        postal_code = profile.postal_code

        address_el = soup.select_one(".gz-card-address")
        if address_el:
            street_el = address_el.select_one(".gz-street-address")
            city_el = address_el.select_one(".gz-address-city")
            state_el = address_el.select_one("[itemprop='addressRegion']")
            postal_el = address_el.select_one("[itemprop='postalCode']")

            if street_el:
                address = self._clean_text(street_el.get_text(" ", strip=True))
            if city_el:
                city = self._clean_text(city_el.get_text(" ", strip=True))
            if state_el:
                state = self._clean_text(state_el.get_text(" ", strip=True))
            if postal_el:
                postal_code = self._clean_text(postal_el.get_text(" ", strip=True))

        hours = ""
        hours_el = soup.select_one(".gz-details-hours p:not(.gz-details-subtitle)")
        if hours_el:
            hours = self._clean_text(hours_el.get_text(" ", strip=True))

        driving_directions = ""
        driving_el = soup.select_one(".gz-details-driving p:not(.gz-details-subtitle)")
        if driving_el:
            driving_directions = self._clean_text(
                driving_el.get_text(" ", strip=True)
            )
        description = ""

        description_selectors = [
            ".gz-details-description",
            ".gz-description",
            ".gz-member-description",
            ".gz-content",
            ".gz-card-description",
            "[itemprop='description']",
        ]

        for selector in description_selectors:
            el = soup.select_one(selector)

            if el:
                description = self._clean_text(
                    el.get_text(" ", strip=True)
                )

                if len(description) > 20:
                    break

        description = re.sub(
            r"^About\s+Us(?:\s+Tab)?\s*",
            "",
            description,
            flags=re.IGNORECASE,
        )

        description = re.sub(
            r"\s+",
            " ",
            description,
        ).strip()

        if self.debug:
            print(
                "DEBUG description:",
                description[:120]
            )
        record = BusinessRecord(
            entity_name=name,
            phone=phone,
            fax=fax,
            email=email,
            website=website,

            facebook=facebook,
            linkedin=linkedin,
            instagram=instagram,
            youtube=youtube,
            twitter=twitter,

            description=description,

            hours=hours,
            driving_directions=driving_directions,

            address=address,
            city=city,
            state=state,
            postal_code=postal_code,

            profile_url=member_url,
            source_url=self.source_url,
            architecture=self.architecture,
            crawl_mode="adapter_chambermaster_profile_extraction",

            category_names=category_names,
        )

        if hasattr(record, "confidence_score"):
            record.confidence_score = self._calculate_confidence(record)
        elif hasattr(record, "confidence"):
            record.confidence = self._calculate_confidence(record)

        return record.to_dict()

    ##############################################################################
    # Crawl Pipeline
    ##############################################################################

    async def crawl(self, page, max_records: int = 5) -> list[dict[str, Any]]:
        """
        ChamberMaster crawl pipeline:

        directory page -> categories -> member profile URLs -> profile extraction
        """
        categories = await self.discover_categories(page)
        self.stats["categories"] = len(categories)

        self._debug("DEBUG ChamberMaster categories found:", len(categories))

        member_urls = await self.discover_member_urls(page, categories)
        self.stats["member_urls"] = len(member_urls)

        self._debug("DEBUG ChamberMaster unique member URLs:", len(member_urls))

        records = []

        for i, member_info in enumerate(member_urls[:max_records], start=1):
            member_url = (
                member_info.get("url", "")
                if isinstance(member_info, dict)
                else str(member_info)
            )

            self._debug(
                f"DEBUG ChamberMaster extracting {i}/{min(len(member_urls), max_records)}: {member_url}"
            )

            try:


                record = await self.extract_member(page, member_info)

                if record:
                    records.append(record)
                    self.stats["profiles_processed"] += 1

            except Exception as e:
                self.stats["profiles_failed"] += 1
                self._debug(
                    "DEBUG ChamberMaster extract_member error:",
                    member_url,
                    repr(e),
                )

        self._debug("DEBUG ChamberMaster crawl returned:", len(records))

        if self.debug:
            print("\n===== ChamberMaster Statistics =====")
            for key, value in self.stats.items():
                print(f"{key:20}: {value}")

        return records

    ##############################################################################
    # Legacy Compatibility
    ##############################################################################

    def extract_listings(self, html: str) -> List[Dict[str, Any]]:
        """
        Legacy single-page extraction fallback.

        This method is kept for compatibility with the generic crawler path.
        The main ChamberMaster production path uses:
        discover_categories() -> discover_member_urls() -> extract_member()
        """
        soup = BeautifulSoup(html or "", "html.parser")

        if self.debug:
            all_links = []

            for a in soup.select("a[href]"):
                href = (a.get("href") or "").strip()
                text = self._clean_text(a.get_text(" ", strip=True))

                if href and (
                        "member" in href.lower()
                        or "list" in href.lower()
                        or "directory" in href.lower()
                        or "category" in href.lower()
                ):
                    all_links.append((text, href))

            print("DEBUG ChamberMaster all relevant links:", all_links[:50])

        records: List[Dict[str, Any]] = []
        seen_urls = set()
        candidates = self._find_candidate_links(soup)

        if self.debug:
            print("DEBUG ChamberMaster candidate sample:", candidates[:20])

        for name, href in candidates:
            profile_url = self._normalize_member_url(
                urljoin(self.source_url, href)
            )

            profile_key = profile_url.lower()

            if profile_key in seen_urls:
                continue

            seen_urls.add(profile_key)

            records.append(
                {
                    "entity_name": name,
                    "profile_url": profile_url,
                    "source_url": self.source_url,
                    "architecture": self.architecture,
                    "crawl_mode": "adapter_chambermaster_legacy_listing",
                    "status": "success",
                    "records_found": 0,
                    "blocked_reason": "",
                }
            )

        total = len(records)

        for record in records:
            record["records_found"] = total

        if self.debug:
            print("DEBUG ChamberMaster candidates:", len(candidates))
            print("DEBUG ChamberMaster returned:", len(records))

        return records

    def _find_candidate_links(self, soup: BeautifulSoup) -> List[tuple[str, str]]:
        candidates: List[tuple[str, str]] = []

        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()
            name = self._clean_text(a.get_text(" ", strip=True))

            if not href or not name:
                continue

            if not self._looks_like_business_link(href):
                continue

            if not self._looks_like_business_name(name):
                continue

            candidates.append((name, href))

        return candidates

    def _looks_like_business_link(self, href: str) -> bool:
        h = href.lower()

        patterns = [
            "/list/member/",
            "/member/",
            "/members/",
            "/directory/",
            "business.hobbschamber.org/list/member",
        ]

        return any(p in h for p in patterns)

    def _looks_like_business_name(self, name: str) -> bool:
        n = name.lower().strip()

        if not n:
            return False

        if n in self.BAD_TEXT:
            return False

        if len(n) < 3:
            return False

        if len(n) > 120:
            return False

        if re.fullmatch(r"[\d\W]+", n):
            return False

        return True
