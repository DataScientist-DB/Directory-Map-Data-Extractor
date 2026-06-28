from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from src.adapters.base import BaseDirectoryAdapter
from src.models.business_record import BusinessRecord


class ChamberMasterAdapter(BaseDirectoryAdapter):
    architecture = "chambermaster"

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.stats = {
            "categories": 0,
            "member_urls": 0,
            "profiles_processed": 0,
            "profiles_failed": 0,
        }

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

    def _extract_next_page(self, html: str) -> str | None:
        """
        Return the URL of the next category page, or None.
        """
        soup = BeautifulSoup(html or "", "html.parser")

        next_link = soup.find(
            "a",
            string=lambda s: s and s.strip().lower() == "next",
        )

        if next_link and next_link.get("href"):
            return urljoin(self.source_url, next_link["href"])

        for a in soup.select("a[href]"):
            text = self._clean_text(a.get_text(" ", strip=True)).lower()
            aria = (a.get("aria-label") or "").strip().lower()
            title = (a.get("title") or "").strip().lower()
            klass = " ".join(a.get("class") or []).lower()

            if "next" in {text, aria, title} or "next" in klass:
                return urljoin(self.source_url, a["href"])

        return None

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

        return round(score, 2)

    async def discover_categories(self, page, html: str = "") -> list[str]:
        if not html:
            html = await page.content()

        return self._extract_category_links(html)

    async def _discover_member_urls_from_category(
        self,
        page,
        category_url: str,
    ) -> list[str]:
        """
        Visit one ChamberMaster category/search page and collect member profile URLs.
        Includes pagination protection.
        """
        urls = set()
        current_url = category_url
        visited_pages = set()

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

            links = self._extract_member_links(html)
            urls.update(links)

            self._debug(
                "DEBUG member links:",
                len(links),
                "total:",
                len(urls),
            )

            current_url = self._extract_next_page(html)

        return sorted(urls)

    async def discover_member_urls(self, page, category_urls: list[str]) -> list[str]:
        """
        Visit all ChamberMaster category/search pages and collect unique member URLs.
        """
        member_urls = set()

        for i, category_url in enumerate(category_urls, start=1):
            try:
                self._debug(
                    f"DEBUG ChamberMaster category {i}/{len(category_urls)}:",
                    category_url,
                )

                urls = await self._discover_member_urls_from_category(
                    page,
                    category_url,
                )

                member_urls.update(urls)

                self._debug(
                    "DEBUG ChamberMaster unique member URLs so far:",
                    len(member_urls),
                )

            except Exception as e:
                self.stats["profiles_failed"] += 1
                self._debug(
                    "DEBUG ChamberMaster category error:",
                    category_url,
                    repr(e),
                )

        result = sorted(member_urls)
        self.stats["member_urls"] = len(result)

        self._debug("DEBUG ChamberMaster total member URLs:", len(result))

        return result

    async def extract_member(self, page, member_url: str) -> dict[str, Any]:
        await page.goto(
            member_url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        await page.wait_for_timeout(500)

        html = await page.content()

        if self.debug:
            debug_dir = Path("debug")
            debug_dir.mkdir(exist_ok=True)

            with open(debug_dir / "member_debug.html", "w", encoding="utf-8") as f:
                f.write(html)

        soup = BeautifulSoup(html or "", "html.parser")

        name = ""
        h1 = soup.select_one(".gz-pagetitle")
        if h1:
            name = self._clean_text(h1.get_text(" ", strip=True))

        phone = ""
        phone_el = soup.select_one(".gz-card-phone span[itemprop='telephone']")
        if phone_el:
            phone = self._clean_text(phone_el.get_text(" ", strip=True))
        fax = ""
        fax_el = soup.select_one(".gz-card-fax span[itemprop='faxNumber']")
        if fax_el:
            fax = self._clean_text(fax_el.get_text(" ", strip=True))


        if fax_el:
            fax = self._clean_text(
                fax_el.get_text(" ", strip=True)
            )

        website = ""
        website_el = soup.select_one(".gz-card-website a[href]")
        if website_el:
            website = (website_el.get("href") or "").strip()

        email = ""
        email_el = soup.select_one(".gz-card-email a[href^='mailto:']")
        if email_el:
            email = email_el.get("href", "").replace("mailto:", "").strip()
        facebook = ""
        linkedin = ""
        instagram = ""
        youtube = ""
        twitter = ""

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

        address = ""
        city = ""
        state = ""
        postal_code = ""

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
        )

        if hasattr(record, "confidence_score"):
            record.confidence_score = self._calculate_confidence(record)
        elif hasattr(record, "confidence"):
            record.confidence = self._calculate_confidence(record)

        return record.to_dict()

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

        for i, member_url in enumerate(member_urls[:max_records], start=1):
            self._debug(
                f"DEBUG ChamberMaster extracting {i}/{min(len(member_urls), max_records)}: {member_url}"
            )

            try:
                record = await self.extract_member(page, member_url)

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

    def extract_listings(self, html: str) -> List[Dict[str, Any]]:
        """
        Legacy single-page extraction fallback.
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
            profile_url = self._normalize_member_url(urljoin(self.source_url, href))

            if profile_url.lower() in seen_urls:
                continue

            seen_urls.add(profile_url.lower())

            records.append(
                {
                    "entity_name": name,
                    "profile_url": profile_url,
                    "source_url": self.source_url,
                    "architecture": self.architecture,
                    "crawl_mode": "adapter_chambermaster",
                }
            )

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
