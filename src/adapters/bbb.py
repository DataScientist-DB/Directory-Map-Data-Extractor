from __future__ import annotations

from typing import Any

from src.adapters.base import BaseDirectoryAdapter
from src.adapters.models import AdapterCapabilities, AdapterInfo


class BBBAdapter(BaseDirectoryAdapter):
    architecture = "bbb"

    INFO = AdapterInfo(
        key="bbb",
        name="Better Business Bureau",
        version="0.1",
        author="Adinfosys",
        website="https://www.bbb.org/",
        description="Placeholder adapter for Better Business Bureau business discovery.",
    )

    CAPABILITIES = AdapterCapabilities(
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

    async def crawl(self, page: Any, max_records: int = 5) -> list[dict[str, Any]]:
        self._debug("DEBUG BBBAdapter is not implemented yet.")
        return []

    def extract_listings(self, html: str) -> list[dict[str, Any]]:
        return []
