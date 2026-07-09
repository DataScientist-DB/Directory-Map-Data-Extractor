from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DiscoveryRequest:
    """
    Universal business discovery request.
    Shared by all directory adapters.
    """

    keyword: str = ""

    location: str = ""

    country: str = ""

    radius_km: int = 0

    accredited_only: bool = False

    max_results: int = 100

    max_pages: int = 10

    request_delay: int = 1500

    sort: str = "Relevance"

    scrape_details: bool = True
