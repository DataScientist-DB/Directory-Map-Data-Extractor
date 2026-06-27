from __future__ import annotations

import re
from typing import Any, Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.adapters.base import BaseDirectoryAdapter


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

    def _extract_category_links(self, html: str) -> list[str]:
        """
        Extract ChamberMaster category URLs from a directory page.
        """

        soup = BeautifulSoup(html, "html.parser")

        categories = set()

        for a in soup.select("a[href]"):

            href = (a.get("href") or "").strip()

            if not href:
                continue

            href_lower = href.lower()

            # Typical ChamberMaster category URLs
            if "/list/category/" in href_lower:
                categories.add(
                    urljoin(self.source_url, href)
                )

            # Some sites use category search URLs
            elif "/list/search" in href_lower:
                categories.add(
                    urljoin(self.source_url, href)
                )

        categories = sorted(categories)

        if self.debug:
            print("DEBUG ChamberMaster categories:", len(categories))

            if categories:
                print(
                    "DEBUG ChamberMaster first categories:",
                    categories[:5],
                )

        return categories

    def _extract_member_links(self, html: str) -> list[str]:
        """
        Extract ChamberMaster member/profile URLs from a category page.
        """
        soup = BeautifulSoup(html or "", "html.parser")

        member_urls = set()

        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()

            if not href:
                continue

            h = href.lower()

            if (
                    "/list/member/" in h
                    or "/member/" in h
            ):
                if "newmemberapp" in h:
                    continue

                member_urls.add(urljoin(self.source_url, href))

        return sorted(member_urls)


    async def discover_categories(self, page, html=""):

        if not html:
            html = await page.content()

        return self._extract_category_links(html)

    async def discover_member_urls(self, page, category_urls):
        """
        Visit ChamberMaster category/search pages and collect member profile URLs.
        """
        member_urls = set()

        for category_url in category_urls:
            try:
                if self.debug:
                    print("DEBUG ChamberMaster visiting category:", category_url)

                await page.goto(
                    category_url,
                    wait_until="domcontentloaded",
                    timeout=30000,
                )

                await page.wait_for_timeout(500)

                html = await page.content()
                links = self._extract_member_links(html)

                if self.debug:
                    print("DEBUG ChamberMaster member links on page:", len(links))

                member_urls.update(links)

            except Exception as e:
                if self.debug:
                    print("DEBUG ChamberMaster category error:", category_url, repr(e))

        result = sorted(member_urls)

        if self.debug:
            print("DEBUG ChamberMaster total member URLs:", len(result))

        return result

    async def extract_member(self, page, member_url):
        await page.goto(member_url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(500)

        html = await page.content()
        soup = BeautifulSoup(html or "", "html.parser")

        text = soup.get_text(" ", strip=True)

        name = ""
        h1 = soup.select_one("h1")
        if h1:
            name = self._clean_text(h1.get_text(" ", strip=True))

        phone = ""
        phone_match = re.search(r"\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}", text)
        if phone_match:
            phone = phone_match.group(0)

        website = ""
        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()
            if href.startswith("http") and "chamber" not in href.lower():
                website = href
                break

        email = ""
        for a in soup.select("a[href^='mailto:']"):
            email = a.get("href", "").replace("mailto:", "").strip()
            break

        return {
            "entity_name": name,
            "phone": phone,
            "website": website,
            "email": email,
            "profile_url": member_url,
            "source_url": self.source_url,
            "architecture": self.architecture,
            "crawl_mode": "adapter_chambermaster_profile_extraction",
        }

    async def crawl(self, page, max_records=50):
        """
        Sprint 2.2.2:
        Full ChamberMaster traversal up to member URL discovery.

        Pipeline:
        directory page -> categories -> member profile URLs

        For now, return lightweight records containing profile URLs.
        Full extract_member() comes in the next sprint.
        """

        categories = await self.discover_categories(page)

        if self.debug:
            print("DEBUG ChamberMaster categories found:", len(categories))

        member_urls = await self.discover_member_urls(page, categories)

        if self.debug:
            print("DEBUG ChamberMaster unique member URLs:", len(member_urls))

        records = []

        for i, member_url in enumerate(member_urls[:max_records], start=1):

            if self.debug:
                print(
                    f"DEBUG ChamberMaster extracting {i}/{min(len(member_urls), max_records)}: {member_url}"
                )

            try:
                record = await self.extract_member(page, member_url)

                if record:
                    records.append(record)

            except Exception as e:
                if self.debug:
                    print(
                        "DEBUG ChamberMaster extract_member error:",
                        member_url,
                        repr(e),
                    )

        if self.debug:
            print("DEBUG ChamberMaster crawl returned:", len(records))

        return records

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