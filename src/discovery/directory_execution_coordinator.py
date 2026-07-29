from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Mapping, Optional

from src.adapters.providers.execution import ProviderExecutionResult
from src.adapters.providers.registry import ProviderRegistry
from src.adapters.providers.request_builder import (
    build_provider_input,
    build_provider_request,
)
from src.crawler import run_crawler
from src.discovery.provider_orchestrator import ProviderOrchestrator
from src.models.provider_status import ProviderStatus


CrawlerCallable = Callable[..., Awaitable[Optional[dict[str, Any]]]]


@dataclass
class DirectoryExecutionOutcome:
    """Normalized outcome for one directory target."""

    directory: str
    target_url: str
    provider_results: list[ProviderExecutionResult] = field(
        default_factory=list
    )
    crawl_results: list[dict[str, Any]] = field(default_factory=list)
    records: list[dict[str, Any]] = field(default_factory=list)


class DirectoryExecutionCoordinator:
    """
    Execute directory targets without directory-specific branches.

    Registered providers run as a priority-ordered fallback chain. Explicit
    legacy/custom architectures without registered providers continue through
    the platform crawler for backward compatibility.
    """

    def __init__(
        self,
        registry: ProviderRegistry,
        *,
        source_input: Mapping[str, Any],
        requested_provider_names: list[str] | None = None,
        local_only: bool = False,
        enable_website_enrichment: bool = False,
        website_timeout_ms: int = 15000,
        legacy_crawler: CrawlerCallable = run_crawler,
    ) -> None:
        self.registry = registry
        self.source_input = dict(source_input)
        self.requested_provider_names = list(
            requested_provider_names or []
        )
        self.local_only = local_only
        self.enable_website_enrichment = enable_website_enrichment
        self.website_timeout_ms = website_timeout_ms
        self.legacy_crawler = legacy_crawler
        self.provider_orchestrator = ProviderOrchestrator(registry)

    async def execute(
        self,
        *,
        directory: str,
        search_url: str,
    ) -> DirectoryExecutionOutcome:
        normalized_directory = str(directory or "").strip().casefold()
        normalized_url = str(search_url or "").strip()

        if not normalized_directory:
            raise ValueError("Directory cannot be empty.")
        if not normalized_url:
            raise ValueError("Directory search URL cannot be empty.")

        if self.registry.has_directory(normalized_directory):
            return await self._execute_registered(
                normalized_directory,
                normalized_url,
            )

        return await self._execute_legacy(
            normalized_directory,
            normalized_url,
        )

    async def _execute_registered(
        self,
        directory: str,
        search_url: str,
    ) -> DirectoryExecutionOutcome:
        request = build_provider_request(
            self.source_input,
            directory,
            search_url,
            enable_website_enrichment=(
                self.enable_website_enrichment
            ),
            website_timeout_ms=self.website_timeout_ms,
        )

        results = await self.provider_orchestrator.search_directory(
            request,
            directory=directory,
            requested_provider_names=self.requested_provider_names,
            local_only=self.local_only,
        )

        if not results:
            return DirectoryExecutionOutcome(
                directory=directory,
                target_url=search_url,
                crawl_results=[
                    self._diagnostic_row(
                        directory=directory,
                        search_url=search_url,
                        status=ProviderStatus.NOT_SUPPORTED.value,
                        reason="no_eligible_provider",
                        detail=(
                            "Registered providers were excluded by the "
                            "requested provider list or local-only policy."
                        ),
                    )
                ],
            )

        records = [
            record
            for result in results
            if (
                result.status.value
                if hasattr(result.status, "value")
                else str(result.status)
            )
            == ProviderStatus.SUCCESS.value
            for record in result.records
            if isinstance(record, dict)
        ]

        return DirectoryExecutionOutcome(
            directory=directory,
            target_url=search_url,
            provider_results=results,
            crawl_results=[
                self._result_row(
                    directory=directory,
                    search_url=search_url,
                    result=result,
                )
                for result in results
            ],
            records=records,
        )

    async def _execute_legacy(
        self,
        directory: str,
        search_url: str,
    ) -> DirectoryExecutionOutcome:
        target_input = build_provider_input(
            self.source_input,
            directory,
            search_url,
        )

        try:
            result = await self.legacy_crawler(
                target_input,
                enable_website_enrichment=(
                    self.enable_website_enrichment
                ),
                website_timeout_ms=self.website_timeout_ms,
            ) or {}
            normalized = dict(result)
            normalized["architecture"] = (
                normalized.get("architecture") or directory
            )
            normalized["directory"] = directory
            normalized["source_url"] = (
                normalized.get("source_url") or search_url
            )
            normalized["target_url"] = search_url
            normalized.setdefault("category_map", {})
            normalized.setdefault("service_map", {})

            return DirectoryExecutionOutcome(
                directory=directory,
                target_url=search_url,
                crawl_results=[normalized],
            )
        except Exception as exc:
            return DirectoryExecutionOutcome(
                directory=directory,
                target_url=search_url,
                crawl_results=[
                    self._diagnostic_row(
                        directory=directory,
                        search_url=search_url,
                        status=ProviderStatus.FAILED.value,
                        reason="legacy_crawler_failed",
                        detail=str(exc),
                    )
                ],
            )

    @staticmethod
    def _result_row(
        *,
        directory: str,
        search_url: str,
        result: ProviderExecutionResult,
    ) -> dict[str, Any]:
        report = result.report
        metadata = report.metadata if report is not None else {}
        raw = metadata.get("crawler_result") or {}
        if not isinstance(raw, Mapping):
            raw = {}

        status = (
            result.status.value
            if hasattr(result.status, "value")
            else str(result.status)
        )
        reported_records = int(
            metadata.get("reported_records_found")
            or raw.get("records_found")
            or (report.records_found if report is not None else 0)
            or 0
        )

        return {
            "architecture": directory,
            "directory": directory,
            "source_url": search_url,
            "target_url": search_url,
            "status": status,
            "records_found": max(
                len(result.records),
                reported_records,
            ),
            "provider": result.provider_name,
            "category_map": dict(raw.get("category_map") or {}),
            "service_map": dict(raw.get("service_map") or {}),
            "access_status": raw.get("access_status", status),
            "access_reason": (
                (report.reason if report is not None else "")
                or raw.get("access_reason")
                or raw.get("blocked_reason")
                or result.error
                or ""
            ),
            "access_http_status": raw.get(
                "access_http_status",
                raw.get("http_status", 0),
            ),
            "access_pages_visited": raw.get(
                "access_pages_visited",
                raw.get("pages_visited", 0),
            ),
            "access_profiles_found": raw.get(
                "access_profiles_found",
                raw.get("profiles_found", 0),
            ),
            "access_recommendation": raw.get(
                "access_recommendation",
                raw.get("recommendation", ""),
            ),
            "external_provider": raw.get("external_provider", {}),
        }

    @staticmethod
    def _diagnostic_row(
        *,
        directory: str,
        search_url: str,
        status: str,
        reason: str,
        detail: str,
    ) -> dict[str, Any]:
        return {
            "architecture": directory,
            "directory": directory,
            "source_url": search_url,
            "target_url": search_url,
            "status": status,
            "records_found": 0,
            "reason": reason,
            "access_reason": detail,
            "category_map": {},
            "service_map": {},
        }
