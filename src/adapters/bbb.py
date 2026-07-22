from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.adapters.base import BaseDirectoryAdapter
from src.adapters.capabilities import AdapterCapabilities
from src.adapters.models import AdapterInfo
from src.models.business_record import BusinessRecord
from src.access.access_analyzer import AccessAnalyzer
# src/adapters/bbb.py



BBB_CAPABILITIES = AdapterCapabilities(
    name="BBB",
    support_level="supported_with_requirements",
    requires_javascript=True,
    requires_proxy=True,
    requires_residential_proxy=True,
    requires_external_proxy_access=True,
    anti_bot_risk="high",
    notes="BBB may trigger Cloudflare Turnstile. Requires suitable residential proxy access."
)

class BBBAdapter(BaseDirectoryAdapter):
    architecture = "bbb"

    INFO = AdapterInfo(
        key="bbb",
        name="Better Business Bureau",
        version="1.0",
        author="Adinfosys",
        website="https://www.bbb.org/",
        description=(
            "Business discovery adapter for Better Business Bureau "
            "directories with Business Intelligence enrichment."
        ),
    )

    CAPABILITIES = AdapterCapabilities(
        name="BBB",
        support_level="supported_with_requirements",
        anti_bot_risk="high",
        requires_javascript=True,
        requires_proxy=True,
        requires_residential_proxy=True,
        requires_external_proxy_access=True,
        notes="BBB may trigger Cloudflare Turnstile and requires suitable proxy access.",

        search=True,
        category_filter=True,
        location_filter=True,
        pagination=True,
        website_links=True,
        social_links=False,
        ratings=True,
        reviews=True,
        contact_details=True,
        business_hours=False,
    )

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    def _slugify_keyword(self, keyword: str) -> str:
        value = self._clean_text(keyword).lower()
        value = re.sub(r"[^a-z0-9]+", "-", value)
        return value.strip("-")

    def _location_to_bbb_path(self, location: str) -> str:
        value = self._clean_text(location).lower()

        state_map = {
            "california": "ca",
            "ca": "ca",
            "texas": "tx",
            "tx": "tx",
            "new york": "ny",
            "ny": "ny",
            "florida": "fl",
            "fl": "fl",
            "illinois": "il",
            "il": "il",
            "arizona": "az",
            "az": "az",
        }

        if "," in value:
            city, state = [x.strip() for x in value.split(",", 1)]
            state_code = state_map.get(state, state[:2])
            city_slug = self._slugify_keyword(city)
            return f"/us/{state_code}/{city_slug}"

        state_code = state_map.get(value, value[:2])
        return f"/us/{state_code}"

    def build_search_url(self) -> str:
        search = self.config.get("search", {}) or {}
        keyword = self._clean_text(search.get("keyword", ""))
        location = self._clean_text(search.get("location", ""))

        if self.source_url:
            return self.source_url

        if not keyword or not location:
            return "https://www.bbb.org/"

        location_path = self._location_to_bbb_path(location)
        category_slug = self._slugify_keyword(keyword)

        return f"https://www.bbb.org{location_path}/category/{category_slug}"

    def _extract_profile_links(self, html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html or "", "html.parser")
        urls: list[str] = []
        seen: set[str] = set()

        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()

            if not href:
                continue

            if "/profile/" not in href.lower():
                continue

            absolute = urljoin(base_url, href).split("?")[0].rstrip("/")

            if absolute not in seen:
                seen.add(absolute)
                urls.append(absolute)

        return urls

    def _extract_next_page(self, html: str, base_url: str) -> str:
        soup = BeautifulSoup(html or "", "html.parser")

        for a in soup.select("a[href]"):
            text = self._clean_text(a.get_text(" ", strip=True)).lower()
            aria = (a.get("aria-label") or "").strip().lower()
            rel = " ".join(a.get("rel") or []).lower()

            if text == "next" or "next" in aria or "next" in rel:
                return urljoin(base_url, a["href"])

        return ""

    async def search(
        self,
        page: Any,
        keyword: str,
        location: str,
        max_pages: int = 5,
    ) -> list[str]:
        search_url = self.build_search_url()
        search = self.config.get("search", {}) or {}

        self.access_report.directory = "Better Business Bureau"
        self.access_report.architecture = self.architecture
        self.access_report.search_keyword = self._clean_text(search.get("keyword", ""))
        self.access_report.search_location = self._clean_text(search.get("location", ""))
        self.access_report.search_url = search_url
        self.access_report.access_strategy = "direct"
        self.access_report.access_strategy = (
            "apify_residential_proxy"
            if self.using_proxy()
            else "direct"
        )
        profile_urls: list[str] = []
        seen: set[str] = set()
        visited: set[str] = set()
        current_url = search_url

        for _ in range(max_pages):
            if not current_url or current_url in visited:
                break

            visited.add(current_url)

            self._debug("DEBUG BBB search page:", current_url)

            response = await page.goto(
                current_url,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            await page.wait_for_timeout(1000)

            html = await page.content()
            http_status = response.status if response else 200

            report = AccessAnalyzer.analyze(
                html=html,
                http_status=http_status,
            )

            self.access_report.status = report.status
            self.access_report.blocked_reason = report.blocked_reason
            self.access_report.http_status = report.http_status
            self.access_report.recommendation = report.recommendation
            self.access_report.pages_visited += 1

            if self.access_report.blocked():
                self._debug(
                    f"BBB blocked: {self.access_report.blocked_reason}"
                )
                return []

            links = self._extract_profile_links(html, current_url)

            for link in links:
                if link not in seen:
                    seen.add(link)
                    profile_urls.append(link)

            self.access_report.profiles_found = len(profile_urls)

            current_url = self._extract_next_page(html, current_url)

        return profile_urls

    async def extract_profile(
        self,
        page: Any,
        profile_url: str,
    ) -> dict[str, Any]:
        await page.goto(
            profile_url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        await page.wait_for_timeout(1000)

        html = await page.content()
        soup = BeautifulSoup(html or "", "html.parser")
        text = self._clean_text(soup.get_text(" ", strip=True))

        title = ""
        h1 = soup.select_one("h1")
        if h1:
            title = self._clean_text(h1.get_text(" ", strip=True))

        phone = ""
        phone_match = re.search(
            r"\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}",
            text,
        )
        if phone_match:
            phone = phone_match.group(0)

        rating = ""
        rating_match = re.search(r"BBB Rating:\s*([A-F][+-]?)", text)
        if rating_match:
            rating = rating_match.group(1)

        accredited = ""
        if "Accredited Business" in text:
            accredited = "Yes"
        elif "not BBB accredited" in text.lower():
            accredited = "No"

        years_in_business = ""
        years_match = re.search(r"Years in Business:\s*(\d+)", text)
        if years_match:
            years_in_business = years_match.group(1)

        website = ""
        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()

            if href.startswith("http") and "bbb.org" not in href.lower():
                website = href
                break

        record = BusinessRecord(
            entity_name=title,
            phone=phone,
            website=website,
            profile_url=profile_url,
            source_url=self.source_url or profile_url,
            architecture=self.architecture,
            crawl_mode="adapter_bbb_profile_extraction",
            category_names="",
            raw_data={
                "bbb_rating": rating,
                "bbb_accredited": accredited,
                "years_in_business": years_in_business,
            },
        )

        return record.to_dict()

    async def crawl(
        self,
        page: Any,
        max_records: int = 100,
    ) -> list[dict[str, Any]]:
        search = self.config.get("search", {}) or {}
        keyword = self._clean_text(search.get("keyword", ""))
        location = self._clean_text(search.get("location", ""))
        max_pages = int(self.config.get("maxPages", 5))

        profile_urls = await self.search(
            page=page,
            keyword=keyword,
            location=location,
            max_pages=max_pages,
        )

        self.access_report.profiles_found = len(profile_urls)

        self._debug("DEBUG BBB profile URLs:", len(profile_urls))

        records: list[dict[str, Any]] = []

        for profile_url in profile_urls[:max_records]:
            try:
                record = await self.extract_profile(page, profile_url)

                if record:
                    records.append(record)

            except Exception as e:
                self._debug(
                    "DEBUG BBB extract_profile error:",
                    profile_url,
                    repr(e),
                )

        if self.debug:
            print("\n===== BBB ACCESS REPORT =====")
            print(f"Status.............. {self.access_report.status}")
            print(f"Reason.............. {self.access_report.blocked_reason}")
            print(f"HTTP Status......... {self.access_report.http_status}")
            print(f"Pages Visited....... {self.access_report.pages_visited}")
            print(f"Profiles Found...... {self.access_report.profiles_found}")
            print(f"Recommendation...... {self.access_report.recommendation}")

        return records

    def extract_listings(self, html: str) -> list[dict[str, Any]]:
        profile_links = self._extract_profile_links(
            html=html,
            base_url=self.source_url or "https://www.bbb.org/",
        )

        return [
            {
                "entity_name": "",
                "website": "",
                "email": "",
                "phone": "",
                "category_names": "",
                "profile_url": profile_url,
                "source_url": self.source_url,
                "architecture": self.architecture,
                "crawl_mode": "adapter_bbb_listing_discovery",
                "status": "profile_discovered",
            }
            for profile_url in profile_links
        ]
