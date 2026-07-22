from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.models.provider_status import ProviderStatus


@dataclass
class ProviderReport:
    """
    Standard execution report returned by every directory provider.
    """

    directory: str
    provider: str
    status: str

    records_found: int = 0
    reason: str = ""

    search_url: str = ""
    run_id: str = ""
    run_status: str = ""
    dataset_id: str = ""

    duration_seconds: float = 0.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    timestamp: str = field(
        default_factory=lambda: datetime.now(
            timezone.utc
        ).isoformat()
    )

    def __post_init__(self) -> None:
        self.directory = str(
            self.directory or ""
        ).strip()

        self.provider = str(
            self.provider or ""
        ).strip()

        self.status = str(
            self.status or ProviderStatus.FAILED.value
        ).strip()

        self.records_found = max(
            int(self.records_found or 0),
            0,
        )

        self.reason = str(
            self.reason or ""
        ).strip()

        self.search_url = str(
            self.search_url or ""
        ).strip()

        self.run_id = str(
            self.run_id or ""
        ).strip()

        self.run_status = str(
            self.run_status or ""
        ).strip()

        self.dataset_id = str(
            self.dataset_id or ""
        ).strip()

        self.duration_seconds = max(
            float(self.duration_seconds or 0.0),
            0.0,
        )

    @property
    def succeeded(self) -> bool:
        return (
            self.status
            == ProviderStatus.SUCCESS.value
        )

    @property
    def usable(self) -> bool:
        return (
            self.succeeded
            and self.records_found > 0
        )

    @property
    def should_fallback(self) -> bool:
        return self.status in {
            ProviderStatus.EMPTY.value,
            ProviderStatus.BLOCKED.value,
            ProviderStatus.DEMO.value,
            ProviderStatus.AUTHENTICATION_FAILED.value,
            ProviderStatus.RENTAL_REQUIRED.value,
            ProviderStatus.ACTOR_UNAVAILABLE.value,
            ProviderStatus.INPUT_ERROR.value,
            ProviderStatus.RATE_LIMITED.value,
            ProviderStatus.RUNTIME_ERROR.value,
            ProviderStatus.FAILED.value,
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
