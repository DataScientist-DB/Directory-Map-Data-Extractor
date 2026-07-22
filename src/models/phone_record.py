from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PhoneRecord:
    number: str

    country_code: str = ""
    extension: str = ""

    classification: str = "office"

    quality_score: int = 0

    confidence: float = 0.0

    source: str = "unknown"
