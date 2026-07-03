from __future__ import annotations

from typing import Any

from src.adapters.base import BaseDirectoryAdapter
from src.adapters.models import AdapterCapabilities, AdapterInfo


class YelpAdapter(BaseDirectoryAdapter):
    architecture = "yelp"

    INFO = AdapterInfo(
        key="yelp",
        name="Yelp",
        version="0.1",
        author="Adinfosys",
        website="https://www.yelp.com/",
        description="Placeholder adapter for Yelp business discovery.",
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
        business_hours=True,
    )

    async def crawl(self, page: Any, max_records: int = 5) -> list[dict[str, Any]]:
        self._debug("DEBUG YelpAdapter is not implemented yet.")
        return []

    def extract_listings(self, html: str) -> list[dict[str, Any]]:
        return []
