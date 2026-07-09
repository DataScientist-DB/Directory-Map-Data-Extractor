from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SearchRequest:
    """
    Universal business search request.
    """

    keyword: str = ""

    services: list[str] = field(default_factory=list)

    products: list[str] = field(default_factory=list)

    industries: list[str] = field(default_factory=list)

    location: str = ""

    country: str = ""

    directories: list[str] = field(default_factory=list)

    accredited_only: bool = False

    sort: str = "Relevance"

    max_results: int = 100
