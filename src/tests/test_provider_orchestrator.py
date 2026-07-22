import pytest

from src.adapters.providers.base_provider import BaseProvider
from src.adapters.providers.registry import ProviderRegistry
from src.discovery.provider_orchestrator import ProviderOrchestrator


class SuccessfulProvider(BaseProvider):

    def __init__(self, name: str, priority: int):
        self._name = name
        self._priority = priority

    def provider_name(self) -> str:
        return self._name

    def capabilities(self) -> dict[str, bool]:
        return {
            "search": True,
            "parallel_safe": True,
        }

    def priority(self) -> int:
        return self._priority

    def search(self, request):
        return [
            {
                "name": f"{self._name} company",
                "source": self._name,
            }
        ]


class AsyncProvider(SuccessfulProvider):

    async def search(self, request):
        return [
            {
                "name": "Async company",
                "source": self.provider_name(),
            }
        ]


class FailingProvider(SuccessfulProvider):

    def search(self, request):
        raise RuntimeError("Provider test failure")


@pytest.mark.asyncio
async def test_orchestrator_runs_providers_by_priority():
    registry = ProviderRegistry()

    registry.register(
        SuccessfulProvider("second", priority=20)
    )
    registry.register(
        SuccessfulProvider("first", priority=10)
    )

    orchestrator = ProviderOrchestrator(registry)
    results = await orchestrator.search({"keyword": "engineer"})

    assert [
        result.provider_name for result in results
    ] == ["first", "second"]

    assert all(
        result.status == "success"
        for result in results
    )


@pytest.mark.asyncio
async def test_orchestrator_supports_async_provider():
    registry = ProviderRegistry()
    registry.register(
        AsyncProvider("async-provider", priority=10)
    )

    orchestrator = ProviderOrchestrator(registry)
    results = await orchestrator.search({})

    assert results[0].status == "success"
    assert len(results[0].records) == 1


@pytest.mark.asyncio
async def test_orchestrator_continues_after_failure():
    registry = ProviderRegistry()

    registry.register(
        FailingProvider("failed", priority=10)
    )
    registry.register(
        SuccessfulProvider("working", priority=20)
    )

    orchestrator = ProviderOrchestrator(registry)
    results = await orchestrator.search({})

    assert results[0].status == "failed"
    assert results[0].error == "Provider test failure"

    assert results[1].status == "success"


@pytest.mark.asyncio
async def test_flatten_records():
    registry = ProviderRegistry()

    registry.register(
        SuccessfulProvider("one", priority=10)
    )
    registry.register(
        SuccessfulProvider("two", priority=20)
    )

    orchestrator = ProviderOrchestrator(registry)
    results = await orchestrator.search({})

    records = orchestrator.flatten_records(results)

    assert len(records) == 2
