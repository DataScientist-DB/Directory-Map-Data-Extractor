from __future__ import annotations

from typing import Any

from src.adapters.capabilities import AdapterCapabilities
from src.adapters.models import AdapterInfo
from src.models.access_report import AccessReport
from src.models.discovery_request import DiscoveryRequest
from src.models.proxy_config import ProxyConfig


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
        self.proxy = self._build_proxy_config()
        self.discovery = self._build_discovery_request()

    def _build_proxy_config(self) -> ProxyConfig:
        proxy = (self.config or {}).get("proxyConfiguration", {}) or {}

        return ProxyConfig(
            use_apify_proxy=bool(proxy.get("useApifyProxy", False)),
            proxy_groups=proxy.get("apifyProxyGroups", []) or [],
            proxy_country=proxy.get("countryCode", ""),
            proxy_url=proxy.get("proxyUrl", ""),
            username=proxy.get("username", ""),
            password=proxy.get("password", ""),
            request_delay=int((self.config or {}).get("requestDelay", 1500)),
        )

    def _build_discovery_request(self) -> DiscoveryRequest:
        search = (self.config or {}).get("search", {}) or {}

        return DiscoveryRequest(
            keyword=search.get("keyword", ""),
            location=search.get("location", ""),
            country=search.get("country", ""),
            accredited_only=bool(search.get("accreditedOnly", False)),
            max_results=int((self.config or {}).get("maxListings", 100)),
            max_pages=int((self.config or {}).get("maxPages", 10)),
            request_delay=int((self.config or {}).get("requestDelay", 1500)),
            sort=search.get("sort", "Relevance"),
            scrape_details=bool((self.config or {}).get("scrapeDetails", True)),
        )

    def using_proxy(self) -> bool:
        return self.proxy.use_apify_proxy or bool(self.proxy.proxy_url)

    @property
    def info(self) -> AdapterInfo:
        return self.INFO

    @property
    def capabilities(self) -> AdapterCapabilities:
        return self.CAPABILITIES

    def _debug(self, *args: Any) -> None:
        if self.debug:
            print(*args)

    async def crawl(
        self,
        page: Any,
        max_records: int = 5,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement crawl()."
        )

    def extract_listings(self, html: str) -> list[dict[str, Any]]:
        return []
