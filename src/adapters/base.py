from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseDirectoryAdapter(ABC):
    """
    Base interface for all architecture-specific directory adapters.
    Every adapter should return normalized business records.
    """

    architecture: str = "unknown"

    def __init__(self, source_url: str = "", debug: bool = False):
        self.source_url = source_url
        self.debug = debug

    @abstractmethod
    def extract_listings(self, html: str) -> List[Dict[str, Any]]:
        """
        Extract business listing records from a directory page.
        Records should use normalized UBDI fields.
        """
        raise NotImplementedError

    def scan(self, html: str) -> Dict[str, Any]:
        """
        Lightweight scan report before full extraction.
        """
        records = self.extract_listings(html)

        return {
            "architecture": self.architecture,
            "source_url": self.source_url,
            "estimated_records": len(records),
            "recommended_strategy": f"{self.architecture}_adapter",
            "status": "adapter_scan_complete",
        }
