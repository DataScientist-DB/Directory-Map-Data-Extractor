from __future__ import annotations

from typing import Any

from src.adapters.models import AdapterCapabilities, AdapterInfo
from src.models.access_report import AccessReport

class BaseDirectoryAdapter:
    architecture = "base"

    INFO = AdapterInfo(
        key="base",
        name="Base Directory Adapter",
        version="1.0",
        description="Base class for UBDIP directory adapters.",
    )

    CAPABILITIES = AdapterCapabilities()

    def __init__(
        self,
        source_url: str = "",
        debug: bool = False,
        config: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self.source_url = source_url
        self.debug = debug
        self.config = config or {}
        self.extra = kwargs
        self.access_report = AccessReport()

    @property
    def info(self) -> AdapterInfo:
        return self.INFO

    @property
    def capabilities(self) -> AdapterCapabilities:
        return self.CAPABILITIES

    def _debug(self, *args: Any) -> None:
        if self.debug:
            print(*args)

    async def crawl(self, page: Any, max_records: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement crawl()."
        )

    def extract_listings(self, html: str) -> list[dict[str, Any]]:
        return []
