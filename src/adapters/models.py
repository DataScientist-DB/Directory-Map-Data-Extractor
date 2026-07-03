from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdapterCapabilities:
    search: bool = False
    category_filter: bool = False
    location_filter: bool = False
    pagination: bool = False
    website_links: bool = False
    social_links: bool = False
    ratings: bool = False
    reviews: bool = False
    contact_details: bool = False
    business_hours: bool = False


@dataclass(frozen=True)
class AdapterInfo:
    key: str
    name: str
    version: str
    author: str = "Adinfosys"
    website: str = ""
    description: str = ""
