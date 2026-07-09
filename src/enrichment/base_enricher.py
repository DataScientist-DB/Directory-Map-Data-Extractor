from __future__ import annotations

from abc import ABC, abstractmethod


class BaseEnricher(ABC):
    """
    Base class for all enrichment modules.
    """

    @abstractmethod
    def enrich(self, website_record):
        raise NotImplementedError
