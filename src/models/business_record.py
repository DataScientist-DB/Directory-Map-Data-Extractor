from dataclasses import dataclass, asdict, field
from typing import Any


@dataclass
class BusinessRecord:
    entity_name: str = ""

    category_names: str = ""
    service_names: str = ""
    products: str = ""
    products_rpc_codes: str = ""
    products_rpc_names: str = ""

    phone: str = ""
    email: str = ""
    website: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
    profile_url: str = ""
    source_url: str = ""
    architecture: str = ""
    crawl_mode: str = ""
    fax: str = ""
    facebook: str = ""
    linkedin: str = ""
    instagram: str = ""
    youtube: str = ""
    twitter: str = ""
    description: str = ""
    hours: str = ""
    driving_directions: str = ""

    business_intelligence_score: int = 0
    contact_completeness: str = ""

    # RC1.1 Business Intelligence Layer
    intelligence_score: int = 0
    intelligence_grade: str = ""

    raw_data: dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
