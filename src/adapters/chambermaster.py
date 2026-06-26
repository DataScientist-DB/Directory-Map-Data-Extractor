from __future__ import annotations

import re
from typing import Any, Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

class ChamberMasterAdapter(BaseDirectoryAdapter):

    architecture = "chambermaster"

    BAD_TEXT = {
        ...
    }

    def extract_listings(self, html: str):
        ...
        return records


    async def discover_categories(self, page, html=""):
        """
        Sprint 2.2
        Will discover category pages from the ChamberMaster directory.
        """
        return []


    async def discover_member_urls(self, page, category_urls):
        """
        Sprint 2.2
        Will visit category pages and collect member URLs.
        """
        return []


    async def extract_member(self, page, member_url):
        """
        Sprint 2.2
        Will visit one member page and extract a complete record.
        """
        return {}


    async def crawl(self, page, max_records=50):
        """
        Temporary implementation.

        Uses the existing parser until the full multi-stage
        ChamberMaster crawler is implemented.
        """
        html = await page.content()
        records = self.extract_listings(html)

        if self.debug:
            print("DEBUG crawl extracted:", len(records))

        return records[:max_records]

    def extract_listings(self, html: str) -> List[Dict[str, Any]]:
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
            profile_url = urljoin(self.source_url, href)

            if profile_url.lower() in seen_urls:
                continue

            seen_urls.add(profile_url)

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

    def _clean_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()