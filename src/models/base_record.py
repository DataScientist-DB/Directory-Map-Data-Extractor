from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BaseRecord:
    """
    Base class for all enrichment records.
    """

    confidence: float = 0.0
    source: str = "unknown"
