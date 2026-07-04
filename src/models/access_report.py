from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AccessReport:
    """
    Records access diagnostics for a directory adapter.
    """

    status: str = "success"
    blocked_reason: str = ""
    http_status: int = 200
    pages_visited: int = 0
    profiles_found: int = 0
    retries: int = 0
    recommendation: str = ""

    def blocked(self) -> bool:
        return self.status == "blocked"

    def succeeded(self) -> bool:
        return self.status == "success"

    def partial(self) -> bool:
        return self.status == "partial"

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "blocked_reason": self.blocked_reason,
            "http_status": self.http_status,
            "pages_visited": self.pages_visited,
            "profiles_found": self.profiles_found,
            "retries": self.retries,
            "recommendation": self.recommendation,
        }
