from __future__ import annotations

from abc import ABC
from typing import Any, Dict, List


class BaseDirectoryAdapter(ABC):
    """
    Base interface for all architecture-specific directory adapters.

    Each adapter should know how to:
    1. discover category/listing pages,
    2. discover member/profile URLs,
    3. extract business profiles,
    4. return normalized UBDI records.
    """

    architecture: str = "unknown"

    def __init__(self, source_url: str = "", debug: bool = False):
        self.source_url = source_url
        self.debug = debug

    def extract_listings(self, html: str) -> List[Dict[str, Any]]:
        """
        Backward-compatible simple extraction method.
        Existing adapters can continue using this.
        """
        return []

    async def discover_categories(self, page, html: str = "") -> List[str]:
        """
        Discover category/search pages from the main directory page.
        """
        return []

    async def discover_member_urls(self, page, category_urls: List[str]) -> List[str]:
        """
        Visit category/search pages and collect member/profile URLs.
        """
        return []

    async def extract_member(self, page, member_url: str) -> Dict[str, Any]:
        """
        Visit one member/profile page and extract a normalized business record.
        """
        return {}

    async def crawl(self, page, max_records: int = 50) -> List[Dict[str, Any]]:
        """
        Full adapter crawler. Platform-specific adapters should override this
        when they support multi-stage crawling.
        """
        html = await page.content()
        return self.extract_listings(html)[:max_records]

    def scan(self, html: str) -> Dict[str, Any]:
        """
        Lightweight scan report before full extraction.
        """
        records = self.extract_listings(html)

        return {
            "architecture": self.architecture,
            "source_url": self.source_url,
            "estimated_records": len(records),
            "recommended_strategy": f"{self.architecture}_adapter",
            "status": "adapter_scan_complete",
        }