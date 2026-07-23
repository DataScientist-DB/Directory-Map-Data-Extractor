from __future__ import annotations

from typing import Any, Dict, Mapping

from src.adapters.external_bbb import ExternalBBBAdapter

from src.adapters.providers.base_provider import BaseProvider
from src.models.provider_result import ProviderResult
from src.models.provider_status import ProviderStatus

class BBBCrawlerBrosProvider(BaseProvider):
    """
    External BBB provider backed by an Apify BBB Actor.

    Expected search request fields:
        search_url
        max_pages
        max_companies
        max_concurrency
        use_apify_proxy
    """

    def __init__(
        self,
        actor_id: str = "ocrad/bbb-company-scraper",
        timeout_seconds: int = 600,
        *,
        provider_enabled: bool = True,
    ) -> None:
        self._actor_id = actor_id
        self._timeout_seconds = timeout_seconds
        self._enabled = provider_enabled

        self._adapter = ExternalBBBAdapter(
            actor_id=actor_id,
            timeout_seconds=timeout_seconds,
        )

        self._last_health = "unknown"
        self._last_report: Dict[str, Any] = {}

    def provider_name(self) -> str:
        return "bbb_external"

    def capabilities(self) -> Dict[str, bool]:
        return {
            "search": True,
            "details": True,
            "enrichment": False,
            "parallel_safe": False,
        }

    def priority(self) -> int:
        return 20

    def enabled(self) -> bool:
        return self._enabled

    def health(self) -> str:
        return self._last_health

    def metadata(self) -> Dict[str, Any]:
        return {
            "directory": "bbb",
            "access_strategy": "external_actor",
            "actor_id": self._actor_id,
            "timeout_seconds": self._timeout_seconds,
            "last_report": self._last_report,
        }

    async def search(
        self,
        request: Mapping[str, Any],
    ) -> ProviderResult:

        search_url = str(request.get("search_url") or "").strip()

        if not search_url:
            raise ValueError(
                "BBBCrawlerBrosProvider requires request['search_url']."
            )

        result = await self._adapter.search(
            search_url=search_url,
            max_pages=int(request.get("max_pages", 10)),
            max_companies=int(request.get("max_companies", 100)),
            max_concurrency=int(request.get("max_concurrency", 5)),
            use_apify_proxy=bool(
                request.get("use_apify_proxy", True)
            ),
        )

        records = list(result.records or [])
        report = result.report

        self._last_report = report.to_dict()

        status = report.status

        if records:
            self._last_health = "healthy"
        elif status == ProviderStatus.BLOCKED.value:
            self._last_health = "blocked"
        elif status in {
            ProviderStatus.FAILED.value,
            ProviderStatus.RUNTIME_ERROR.value,
        }:
            self._last_health = "unavailable"
        else:
            self._last_health = "degraded"

        return result
    
