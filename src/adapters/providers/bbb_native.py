from __future__ import annotations

from copy import deepcopy
from typing import Any, Awaitable, Callable, Dict, Mapping, Optional

from src.adapters.providers.base_provider import BaseProvider
from src.crawler import run_crawler
from src.models.provider_report import ProviderReport
from src.models.provider_result import ProviderResult
from src.models.provider_status import ProviderStatus

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
    ) -> ProviderResult:

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

        raw_status = str(
            result.get("access_status")
            or result.get("status")
            or ""
        ).strip().lower()

        status_aliases = {
            "success": ProviderStatus.SUCCESS.value,
            "succeeded": ProviderStatus.SUCCESS.value,
            "completed": ProviderStatus.SUCCESS.value,
            "empty": ProviderStatus.EMPTY.value,
            "no_results": ProviderStatus.EMPTY.value,
            "blocked": ProviderStatus.BLOCKED.value,
            "authentication_failed": (
                ProviderStatus.AUTHENTICATION_FAILED.value
            ),
            "rental_required": ProviderStatus.RENTAL_REQUIRED.value,
            "actor_unavailable": (
                ProviderStatus.ACTOR_UNAVAILABLE.value
            ),
            "input_error": ProviderStatus.INPUT_ERROR.value,
            "rate_limited": ProviderStatus.RATE_LIMITED.value,
            "timeout": ProviderStatus.TIMEOUT.value,
            "network_error": ProviderStatus.NETWORK_ERROR.value,
            "not_supported": ProviderStatus.NOT_SUPPORTED.value,
            "runtime_error": ProviderStatus.RUNTIME_ERROR.value,
            "error": ProviderStatus.RUNTIME_ERROR.value,
            "failed": ProviderStatus.FAILED.value,
        }

        status = status_aliases.get(
            raw_status,
            ProviderStatus.FAILED.value,
        )

        reported_records_found = int(
            result.get("records_found") or 0
        )

        reason = str(
            result.get("blocked_reason")
            or result.get("access_reason")
            or result.get("reason")
            or ""
        ).strip()

        if status == ProviderStatus.SUCCESS.value:
            self._last_health = "healthy"
        elif status == ProviderStatus.BLOCKED.value:
            self._last_health = "blocked"
        elif status in {
            ProviderStatus.FAILED.value,
            ProviderStatus.RUNTIME_ERROR.value,
            ProviderStatus.NETWORK_ERROR.value,
            ProviderStatus.TIMEOUT.value,
        }:
            self._last_health = "unavailable"
        else:
            self._last_health = "degraded"

        report = ProviderReport(
            directory="bbb",
            provider=self.provider_name(),
            status=status,
            reason=reason,
            search_url=search_url,
            metadata={
                "crawler_result": dict(result),
                "reported_records_found": reported_records_found,
                "access_status": result.get("access_status", ""),
                "access_reason": result.get("access_reason", ""),
                "http_status": result.get(
                    "access_http_status",
                    result.get("http_status", 0),
                ),
                "pages_visited": result.get(
                    "access_pages_visited",
                    result.get("pages_visited", 0),
                ),
                "profiles_found": result.get(
                    "access_profiles_found",
                    result.get("profiles_found", 0),
                ),
                "recommendation": result.get(
                    "access_recommendation",
                    result.get("recommendation", ""),
                ),
            },
        )

        # run_crawler writes company and diagnostic rows directly to the
        # Actor dataset. Its return value contains execution metadata rather
        # than the extracted company records.
        return ProviderResult(
            records=[],
            report=report,
        )
