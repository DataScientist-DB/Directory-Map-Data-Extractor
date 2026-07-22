from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AccessReport:
    """
    Records access diagnostics for a directory adapter.
    """

    # ==========================================================
    # Request information
    # ==========================================================

    directory: str = ""
    architecture: str = ""

    search_keyword: str = ""
    search_location: str = ""

    search_url: str = ""
    requested_url: str = ""
    access_strategy: str = "direct"

    # ==========================================================
    # Access diagnostics
    # ==========================================================

    status: str = "success"
    blocked_reason: str = ""

    http_status: int = 200

    pages_visited: int = 0
    profiles_found: int = 0

    retries: int = 0

    recommendation: str = ""

    # ==========================================================
    # Execution statistics
    # ==========================================================

    records_exported: int = 0

    started_at: str = ""
    finished_at: str = ""
    elapsed_seconds: float = 0.0

    # ==========================================================
    # Helper methods
    # ==========================================================

    def blocked(self) -> bool:
        return self.status == "blocked"

    def succeeded(self) -> bool:
        return self.status == "success"

    def partial(self) -> bool:
        return self.status == "partial"

    def to_dict(self) -> dict[str, object]:
        return {
            # Request
            "directory": self.directory,
            "architecture": self.architecture,
            "search_keyword": self.search_keyword,
            "search_location": self.search_location,
            "search_url": self.search_url,
            "requested_url": self.requested_url,

            # Access
            "status": self.status,
            "blocked_reason": self.blocked_reason,
            "http_status": self.http_status,
            "pages_visited": self.pages_visited,
            "profiles_found": self.profiles_found,
            "retries": self.retries,
            "recommendation": self.recommendation,

            # Statistics
            "records_exported": self.records_exported,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "elapsed_seconds": self.elapsed_seconds,
            "access_strategy": self.access_strategy,
        }
