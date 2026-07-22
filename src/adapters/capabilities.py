# src/adapters/capabilities.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


SupportLevel = Literal[
    "fully_supported",
    "supported_with_requirements",
    "experimental",
    "disabled",
]

AntiBotRisk = Literal[
    "low",
    "medium",
    "high",
]


@dataclass
class AdapterCapabilities:
    # Product/support metadata
    name: str = ""
    support_level: SupportLevel = "experimental"
    anti_bot_risk: AntiBotRisk = "low"
    notes: str = ""

    # Access requirements
    requires_javascript: bool = True
    requires_proxy: bool = False
    requires_residential_proxy: bool = False
    requires_external_proxy_access: bool = False

    # Discovery capabilities
    search: bool = False
    category_filter: bool = False
    location_filter: bool = False
    pagination: bool = False

    # Data capabilities
    website_links: bool = False
    social_links: bool = False
    ratings: bool = False
    reviews: bool = False
    contact_details: bool = False
    business_hours: bool = False
