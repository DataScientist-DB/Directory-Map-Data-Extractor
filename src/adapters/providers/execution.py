from dataclasses import dataclass, field
from typing import Any, List, Optional

from src.models.provider_report import ProviderReport


@dataclass
class ProviderExecutionResult:
    """
    Normalized result produced by ProviderOrchestrator.

    Supports both:
    - legacy providers returning lists or tuples
    - structured providers returning ProviderResult
    """

    provider_name: str
    status: str
    records: List[Any] = field(default_factory=list)
    error: Optional[str] = None
    report: Optional[ProviderReport] = None
    requires_fallback: bool = False

    @property
    def succeeded(self) -> bool:
        return self.status == "success"

    @property
    def usable(self) -> bool:
        return self.succeeded and bool(self.records)
