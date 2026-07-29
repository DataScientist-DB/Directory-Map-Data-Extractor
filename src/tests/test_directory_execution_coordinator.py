from typing import Any

import pytest

from src.adapters.providers.base_provider import BaseProvider
from src.adapters.providers.bootstrap import build_provider_registry
from src.discovery.directory_execution_coordinator import (
    DirectoryExecutionCoordinator,
)
from src.models.provider_report import ProviderReport
from src.models.provider_result import ProviderResult
from src.models.provider_status import ProviderStatus


class DirectoryProvider(BaseProvider):
    def __init__(
        self,
        name: str,
        *,
        directory: str,
        status: str,
        provider_priority: int,
        access_strategy: str = "native_adapter",
        records: list[dict[str, Any]] | None = None,
    ) -> None:
        self._name = name
        self._directory = directory
        self._status = status
        self._priority = provider_priority
        self._access_strategy = access_strategy
        self._records = records or []

    def provider_name(self) -> str:
        return self._name

    def capabilities(self) -> dict[str, bool]:
        return {"search": True}

    def priority(self) -> int:
        return self._priority

    def metadata(self) -> dict[str, Any]:
        return {
            "directory": self._directory,
            "access_strategy": self._access_strategy,
        }

    def search(self, request: Any) -> ProviderResult:
        return ProviderResult(
            records=self._records,
            report=ProviderReport(
                directory=self._directory,
                provider=self._name,
                status=self._status,
                reason="test reason",
                search_url=request["search_url"],
            ),
        )


def _bbb_registry():
    return build_provider_registry(
        [
            DirectoryProvider(
                "bbb_external",
                directory="bbb",
                status=ProviderStatus.BLOCKED.value,
                provider_priority=20,
                access_strategy="external_actor",
            ),
            DirectoryProvider(
                "bbb_native",
                directory="bbb",
                status=ProviderStatus.SUCCESS.value,
                provider_priority=30,
                records=[{"name": "Example Business"}],
            ),
        ]
    )


@pytest.mark.asyncio
async def test_registered_directory_uses_generic_fallback_chain():
    coordinator = DirectoryExecutionCoordinator(
        _bbb_registry(),
        source_input={"maxListings": 10},
    )

    outcome = await coordinator.execute(
        directory="bbb",
        search_url="https://www.bbb.org/search?find_text=engineers",
    )

    assert [
        result.provider_name
        for result in outcome.provider_results
    ] == ["bbb_external", "bbb_native"]
    assert outcome.records == [{"name": "Example Business"}]
    assert len(outcome.crawl_results) == 2


@pytest.mark.asyncio
async def test_non_success_fallback_records_are_not_exported():
    registry = build_provider_registry(
        [
            DirectoryProvider(
                "demo_provider",
                directory="bbb",
                status=ProviderStatus.DEMO.value,
                provider_priority=10,
                records=[{"name": "Demo Business"}],
            ),
            DirectoryProvider(
                "native_provider",
                directory="bbb",
                status=ProviderStatus.SUCCESS.value,
                provider_priority=20,
                records=[{"name": "Production Business"}],
            ),
        ]
    )
    coordinator = DirectoryExecutionCoordinator(
        registry,
        source_input={},
    )

    outcome = await coordinator.execute(
        directory="bbb",
        search_url="https://www.bbb.org/search?find_text=engineers",
    )

    assert outcome.records == [{"name": "Production Business"}]


@pytest.mark.asyncio
async def test_local_only_excludes_external_provider():
    coordinator = DirectoryExecutionCoordinator(
        _bbb_registry(),
        source_input={},
        local_only=True,
    )

    outcome = await coordinator.execute(
        directory="bbb",
        search_url="https://www.bbb.org/search?find_text=engineers",
    )

    assert [
        result.provider_name
        for result in outcome.provider_results
    ] == ["bbb_native"]


@pytest.mark.asyncio
async def test_explicit_provider_filter_is_respected():
    coordinator = DirectoryExecutionCoordinator(
        _bbb_registry(),
        source_input={},
        requested_provider_names=["bbb_native"],
    )

    outcome = await coordinator.execute(
        directory="bbb",
        search_url="https://www.bbb.org/search?find_text=engineers",
    )

    assert [
        result.provider_name
        for result in outcome.provider_results
    ] == ["bbb_native"]


@pytest.mark.asyncio
async def test_no_eligible_registered_provider_returns_diagnostic():
    coordinator = DirectoryExecutionCoordinator(
        _bbb_registry(),
        source_input={},
        requested_provider_names=["unknown_provider"],
    )

    outcome = await coordinator.execute(
        directory="bbb",
        search_url="https://www.bbb.org/search?find_text=engineers",
    )

    assert outcome.provider_results == []
    assert outcome.crawl_results[0]["status"] == "not_supported"
    assert (
        outcome.crawl_results[0]["reason"]
        == "no_eligible_provider"
    )


@pytest.mark.asyncio
async def test_unregistered_directory_uses_legacy_crawler():
    captured_input: dict[str, Any] = {}

    async def legacy_crawler(input_data, **kwargs):
        captured_input.update(input_data)
        return {
            "status": "success",
            "records_found": 3,
            "category_map": {"a": "Category"},
        }

    coordinator = DirectoryExecutionCoordinator(
        build_provider_registry([]),
        source_input={"mode": "auto"},
        legacy_crawler=legacy_crawler,
    )

    outcome = await coordinator.execute(
        directory="custom_directory",
        search_url="https://example.com/directory",
    )

    assert captured_input["architecture"] == "custom_directory"
    assert captured_input["search"]["directories"] == [
        "custom_directory"
    ]
    assert outcome.crawl_results[0]["records_found"] == 3
    assert outcome.crawl_results[0]["directory"] == "custom_directory"


@pytest.mark.asyncio
async def test_legacy_crawler_failure_is_normalized():
    async def failing_crawler(input_data, **kwargs):
        raise RuntimeError("test crawler failure")

    coordinator = DirectoryExecutionCoordinator(
        build_provider_registry([]),
        source_input={},
        legacy_crawler=failing_crawler,
    )

    outcome = await coordinator.execute(
        directory="custom_directory",
        search_url="https://example.com/directory",
    )

    row = outcome.crawl_results[0]
    assert row["status"] == "failed"
    assert row["reason"] == "legacy_crawler_failed"
    assert row["access_reason"] == "test crawler failure"
