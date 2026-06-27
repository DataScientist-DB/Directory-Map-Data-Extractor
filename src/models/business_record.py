from dataclasses import dataclass, asdict, field
from typing import Any


@dataclass
class BusinessRecord:
    entity_name: str = ""
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

    raw_data: dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)