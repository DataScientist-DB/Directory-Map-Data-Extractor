from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.models.provider_report import ProviderReport


@dataclass
class ProviderResult:
    """
    Standard result returned by every directory provider.
    """

    records: list[dict[str, Any]] = field(
        default_factory=list
    )

    report: ProviderReport | None = None

    def __post_init__(self) -> None:
        self.records = [
            record
            for record in self.records
            if isinstance(record, dict)
        ]

        if self.report is None:
            raise ValueError(
                "ProviderResult requires a ProviderReport."
            )

        self.report.records_found = len(
            self.records
        )

    @property
    def succeeded(self) -> bool:
        return self.report.succeeded

    @property
    def usable(self) -> bool:
        return self.report.usable

    @property
    def should_fallback(self) -> bool:
        return self.report.should_fallback

    def to_dict(self) -> dict[str, Any]:
        return {
            "records": self.records,
            "report": self.report.to_dict(),
        }
