import pytest

from src.adapters.providers.base_provider import BaseProvider
from src.adapters.providers.registry import ProviderRegistry


class TestProvider(BaseProvider):

    def __init__(
        self,
        name: str,
        *,
        provider_priority: int = 100,
        provider_enabled: bool = True,
        search_enabled: bool = True,
    ) -> None:
        self._name = name
        self._priority = provider_priority
        self._enabled = provider_enabled
        self._search_enabled = search_enabled

    def provider_name(self) -> str:
        return self._name

    def capabilities(self) -> dict[str, bool]:
        return {
            "search": self._search_enabled,
            "details": False,
            "enrichment": False,
            "parallel_safe": True,
        }

    def search(self, request):
        return [{"provider": self._name}]

    def priority(self) -> int:
        return self._priority

    def enabled(self) -> bool:
        return self._enabled


def test_register_and_get_provider():
    registry = ProviderRegistry()
    provider = TestProvider("provider-a")

    registry.register(provider)

    assert registry.get("provider-a") is provider
    assert registry.names() == ["provider-a"]


def test_duplicate_registration_is_rejected():
    registry = ProviderRegistry()
    registry.register(TestProvider("provider-a"))

    with pytest.raises(ValueError):
        registry.register(TestProvider("provider-a"))


def test_enabled_providers_are_sorted_by_priority():
    registry = ProviderRegistry()

    registry.register(
        TestProvider("low-priority", provider_priority=50)
    )
    registry.register(
        TestProvider("high-priority", provider_priority=10)
    )
    registry.register(
        TestProvider(
            "disabled",
            provider_priority=1,
            provider_enabled=False,
        )
    )

    names = [
        provider.provider_name()
        for provider in registry.enabled()
    ]

    assert names == ["high-priority", "low-priority"]


def test_filter_by_capability():
    registry = ProviderRegistry()

    registry.register(
        TestProvider("search-provider", search_enabled=True)
    )
    registry.register(
        TestProvider("no-search-provider", search_enabled=False)
    )

    names = [
        provider.provider_name()
        for provider in registry.by_capability("search")
    ]

    assert names == ["search-provider"]


def test_select_highest_priority_provider():
    registry = ProviderRegistry()

    registry.register(
        TestProvider("second", provider_priority=20)
    )
    registry.register(
        TestProvider("first", provider_priority=10)
    )

    selected = registry.select(capability="search")

    assert selected.provider_name() == "first"


def test_select_named_provider():
    registry = ProviderRegistry()
    registry.register(TestProvider("provider-a"))

    selected = registry.select(
        name="provider-a",
        capability="search",
    )

    assert selected.provider_name() == "provider-a"
