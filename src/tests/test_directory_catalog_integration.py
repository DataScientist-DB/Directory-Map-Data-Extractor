from typing import Any

from src.adapters.providers.base_provider import BaseProvider
from src.adapters.providers.registry import ProviderRegistry
from src.discovery.directory_catalog import get_directory_by_id
from src.discovery.search_orchestrator import SearchOrchestrator
from src.discovery.search_plan import build_search_plan


class StubProvider(BaseProvider):
    def __init__(
        self,
        name: str,
        directory: str,
        provider_priority: int,
    ) -> None:
        self._name = name
        self._directory = directory
        self._priority = provider_priority

    def provider_name(self) -> str:
        return self._name

    def capabilities(self) -> dict[str, bool]:
        return {"search": True}

    def priority(self) -> int:
        return self._priority

    def metadata(self) -> dict[str, Any]:
        return {"directory": self._directory}

    def search(self, request: Any) -> list[Any]:
        return []


def test_catalog_source_compatibility_properties():
    bbb = get_directory_by_id("BBB")

    assert bbb is not None
    assert bbb.provider == "bbb"
    assert bbb.is_general
    assert bbb.supports_country("United States")
    assert not bbb.supports_country("Armenia")


def test_registry_resolves_directory_to_best_provider():
    registry = ProviderRegistry()
    registry.register(StubProvider("bbb_native", "bbb", 30))
    registry.register(StubProvider("bbb_external", "bbb", 20))

    selected = registry.select_for_directory("BBB")

    assert selected.provider_name() == "bbb_external"
    assert registry.directory_names() == {"bbb"}


def test_orchestrator_uses_registered_directories_only():
    registry = ProviderRegistry()
    registry.register(StubProvider("bbb_external", "bbb", 20))
    registry.register(
        StubProvider("chambermaster", "chambermaster", 30)
    )
    orchestrator = SearchOrchestrator(registry=registry)

    directories = orchestrator.get_directories(
        {
            "keyword": "traffic engineers",
            "location": "Phoenix, AZ",
            "country": "USA",
        }
    )

    assert directories == ["bbb", "chambermaster"]


def test_explicit_targets_remain_backward_compatible():
    orchestrator = SearchOrchestrator()

    targets = orchestrator.build_targets(
        {
            "directoryTargets": [
                {
                    "directory": "bbb",
                    "url": "https://www.bbb.org/example",
                },
                {
                    "architecture": "BBB",
                    "url": "https://www.bbb.org/example/",
                },
            ]
        },
        {},
    )

    assert targets == [
        {
            "directory": "bbb",
            "url": "https://www.bbb.org/example",
        }
    ]


def test_search_plan_is_serializable():
    orchestrator = SearchOrchestrator()
    orchestrator.get_directories(
        {
            "keyword": "traffic engineers",
            "location": "Phoenix, AZ",
            "country": "USA",
        }
    )

    selection = orchestrator.selector.last_selection
    assert selection is not None

    plan = build_search_plan(selection)

    assert plan["industry"] == "traffic engineering"
    assert isinstance(plan["directories_selected"], list)
