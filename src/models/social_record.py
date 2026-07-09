from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SocialRecord:
    """
    Represents a social media profile discovered on a website.
    """

    platform: str
    url: str

    verified: bool = False

    quality_score: int = 0

    confidence: float = 0.0

    source: str = "unknown"
