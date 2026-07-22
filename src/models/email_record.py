# src/models/email_record.py

from dataclasses import dataclass


@dataclass
class EmailRecord:
    email: str
    local_part: str
    domain: str
    classification: str = "unknown"
    quality_score: int = 0
    confidence: float = 0.0
    source: str = "unknown"
