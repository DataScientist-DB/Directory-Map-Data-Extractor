from __future__ import annotations

from copy import deepcopy
from typing import Any, Awaitable, Callable, Dict, Mapping, Optional

from src.adapters.providers.base_provider import BaseProvider
from src.crawler import run_crawler


CrawlerCallable = Callable[..., Awaitable[Optional[dict[str, Any]]]]


class BBBNativeProvider(BaseProvider):
    """
    Native BBB provider backed by the platform's existing crawler.

    Expected search request fields:
        input_data
        search_url
        enable_website_enrichment
        website_timeout_ms
    """

    def __init__(
        self,
        *,
        crawler: CrawlerCallable = run_crawler,
        provider_enabled: bool = True,
    ) -> None:
        self._crawler = crawler
        self._enabled = provider_enabled
        self._last_health = "unknown"
        self._last_result: Dict[str, Any] = {}

    def provider_name(self) -> str:
        return "bbb_native"

    def capabilities(self) -> Dict[str, bool]:
        return {
            "search": True,
            "details": True,
            "enrichment": True,
            "parallel_safe": False,
        }

    def priority(self) -> int:
        return 30

    def enabled(self) -> bool:
        return self._enabled

    def health(self) -> str:
        return self._last_health

    def metadata(self) -> Dict[str, Any]:
        return {
            "directory": "bbb",
            "access_strategy": "native_browser",
            "last_result": self._last_result,
        }

    async def search(
        self,
        request: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        source_input = request.get("input_data")

        if not isinstance(source_input, Mapping):
            raise ValueError(
                "BBBNativeProvider requires request['input_data'] "
                "to be a mapping."
            )

        search_url = str(request.get("search_url") or "").strip()

        if not search_url:
            raise ValueError(
                "BBBNativeProvider requires request['search_url']."
            )

        target_input = deepcopy(dict(source_input))
        target_input["architecture"] = "bbb"
        target_input["startUrls"] = [{"url": search_url}]

        target_search = dict(target_input.get("search") or {})
        target_search["directories"] = ["bbb"]
        target_search["autoSelectDirectories"] = False
        target_input["search"] = target_search

        result = await self._crawler(
            target_input,
            enable_website_enrichment=bool(
                request.get(
                    "enable_website_enrichment",
                    False,
                )
            ),
            website_timeout_ms=int(
                request.get(
                    "website_timeout_ms",
                    15000,
                )
            ),
        ) or {}

        self._last_result = dict(result)

        status = str(result.get("status") or "").strip().lower()
        records_found = int(result.get("records_found") or 0)

        if records_found > 0 or status == "success":
            self._last_health = "healthy"
        elif status == "blocked":
            self._last_health = "blocked"
        elif status in {"failed", "error"}:
            self._last_health = "unavailable"
        else:
            self._last_health = "degraded"

        # run_crawler pushes records directly into the Actor dataset.
        # Its return value is crawl metadata rather than the record list.
        return []
