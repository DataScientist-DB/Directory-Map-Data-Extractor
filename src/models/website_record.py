from __future__ import annotations

from dataclasses import dataclass, field

from src.models.email_record import EmailRecord
from src.models.phone_record import PhoneRecord
from src.models.social_record import SocialRecord
from src.models.schema_record import SchemaRecord


@dataclass(slots=True)
class WebsiteRecord:
    """
    Canonical representation of a company's website.

    Every enrichment module contributes to this object.
    """

    # Basic
    url: str = ""
    title: str = ""
    description: str = ""

    # Contact intelligence
    email_records: list[EmailRecord] = field(default_factory=list)
    phone_records: list[PhoneRecord] = field(default_factory=list)

    # Social presence
    social_records: list[SocialRecord] = field(default_factory=list)

    # Structured data
    schema_records: list[SchemaRecord] = field(default_factory=list)

    # Website quality
    quality_score: int = 0
    quality_grade: str = ""

    # Intelligence
    confidence: float = 0.0

    # Summary values (for exporters)
    primary_email: str = ""
    primary_phone: str = ""

    has_contact_page: bool = False
    has_about_page: bool = False
    has_schema: bool = False
