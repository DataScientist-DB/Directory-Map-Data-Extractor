from __future__ import annotations

from abc import ABC, abstractmethod


class BaseExtractor(ABC):
    """
    Base class for all enrichment extractors.
    """

    @abstractmethod
    def extract(self, html: str):
        """Extract structured records from HTML."""
        raise NotImplementedError
