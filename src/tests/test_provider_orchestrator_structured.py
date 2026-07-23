import pytest

from src.adapters.providers.base_provider import BaseProvider
from src.adapters.providers.bootstrap import build_provider_registry
from src.discovery.provider_orchestrator import ProviderOrchestrator
from src.models.provider_report import ProviderReport
from src.models.provider_result import ProviderResult
from src.models.provider_status import ProviderStatus


class StructuredProvider(BaseProvider):
    def __init__(
        self,
        name: str,
        status: str,
        records: list[dict] | None = None,
    ) -> None:
        self._name = name
        self._status = status
        self._records = records or []

    def provider_name(self) -> str:
        return self._name

    def capabilities(self) -> dict[str, bool]:
        return {"search": True}

    def search(self, request):
        return ProviderResult(
            records=self._records,
            report=ProviderReport(
                directory="bbb",
                provider=self._name,
                status=self._status,
                reason="test reason",
            ),
        )


@pytest.mark.asyncio
async def test_preserves_structured_provider_result():
    provider = StructuredProvider(
        "bbb_external",
        ProviderStatus.BLOCKED.value,
    )

    registry = build_provider_registry([provider])
    orchestrator = ProviderOrchestrator(registry)

    results = await orchestrator.search(
        {},
        provider_names=["bbb_external"],
    )

    assert results[0].status == ProviderStatus.BLOCKED.value
    assert results[0].requires_fallback is True
    assert results[0].report is not None


@pytest.mark.asyncio
async def test_runs_native_fallback():
    external = StructuredProvider(
        "bbb_external",
        ProviderStatus.RATE_LIMITED.value,
    )
    native = StructuredProvider(
        "bbb_native",
        ProviderStatus.SUCCESS.value,
        records=[{"name": "Example Business"}],
    )

    registry = build_provider_registry([external, native])
    orchestrator = ProviderOrchestrator(registry)

    results = await orchestrator.search_with_fallback(
        {},
        primary_name="bbb_external",
        fallback_name="bbb_native",
        fallback_enabled=True,
    )

    assert len(results) == 2
    assert results[0].provider_name == "bbb_external"
    assert results[1].provider_name == "bbb_native"
    assert results[1].usable is True
