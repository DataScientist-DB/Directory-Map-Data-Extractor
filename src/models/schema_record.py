from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SchemaRecord:
    """
    Represents a single Schema.org entity found on a webpage.
    """

    schema_type: str

    properties: dict[str, object] = field(default_factory=dict)

    quality_score: int = 0

    confidence: float = 0.0

    source: str = "unknown"
