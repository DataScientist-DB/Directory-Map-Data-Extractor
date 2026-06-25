from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.adapters.base import BaseDirectoryAdapter


class ChamberMasterAdapter(BaseDirectoryAdapter):
    architecture = "chambermaster"

    def extract_listings(self, html: str) -> List[Dict[str, Any]]:
        """
        Milestone 1 placeholder:
        Extract basic ChamberMaster profile links and visible names.
        Full extraction will be added in Milestone 2.
        """
        soup = BeautifulSoup(html or "", "html.parser")
        records: List[Dict[str, Any]] = []
        seen = set()

        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()
            text = " ".join(a.get_text(" ", strip=True).split())

            if not href or not text:
                continue

            href_l = href.lower()

            if not any(x in href_l for x in ["/member/", "/list/member/", "/directory/"]):
                continue

            profile_url = urljoin(self.source_url, href)

            key = (text.lower(), profile_url.lower())
            if key in seen:
                continue

            seen.add(key)

            records.append(
                {
                    "entity_name": text,
                    "profile_url": profile_url,
                    "source_url": self.source_url,
                    "architecture": self.architecture,
                    "crawl_mode": "adapter_chambermaster",
                }
            )

        return records
