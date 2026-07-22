from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class ProviderExecutionResult:
    provider_name: str
    status: str
    records: List[Any] = field(default_factory=list)
    error: Optional[str] = None
