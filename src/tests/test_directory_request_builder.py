from urllib.parse import parse_qs, urlparse

from src.adapters.providers.base_provider import BaseProvider
from src.adapters.providers.registry import ProviderRegistry
from src.discovery.directory_request_builder import build_bbb_search_url
from src.discovery.search_orchestrator import SearchOrchestrator
from src.models.search_request import SearchRequest


class StubProvider(BaseProvider):
    def __init__(
        self,
        name: str,
        directory: str,
        provider_priority: int = 20,
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

    def metadata(self) -> dict[str, str]:
        return {"directory": self._directory}

    def search(self, request):
        return []


def _runtime_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register(StubProvider("bbb_external", "bbb"))
    registry.register(
        StubProvider("chambermaster", "chambermaster", 30)
    )
    return registry


def test_builds_encoded_bbb_search_url():
    url = build_bbb_search_url(
        query="traffic engineers",
        location="Phoenix, AZ",
        country="USA",
    )

    assert url is not None
    parsed = urlparse(url)
    parameters = parse_qs(parsed.query)

    assert parsed.netloc == "www.bbb.org"
    assert parameters["find_text"] == ["traffic engineers"]
    assert parameters["find_loc"] == ["Phoenix, AZ"]
    assert parameters["find_country"] == ["USA"]


def test_auto_plan_generates_bbb_and_skips_chambermaster():
    orchestrator = SearchOrchestrator(registry=_runtime_registry())
    request = SearchRequest(
        keyword="traffic engineers",
        location="Phoenix, AZ",
        country="USA",
    )

    targets = orchestrator.build_targets({}, request)
    details = orchestrator.execution_details()

    assert len(targets) == 1
    assert targets[0]["directory"] == "bbb"
    assert targets[0]["url"].startswith("https://www.bbb.org/search?")
    assert details is not None
    assert {
        item["directory"]: item["reason"]
        for item in details["skipped"]
    }["chambermaster"] == "explicit_url_required"


def test_requested_chambermaster_without_url_is_skipped():
    orchestrator = SearchOrchestrator(registry=_runtime_registry())
    request = SearchRequest(
        keyword="roofing contractors",
        location="Phoenix, AZ",
        country="USA",
        directories=["chambermaster"],
    )

    assert orchestrator.build_targets({}, request) == []
    details = orchestrator.execution_details()
    assert details is not None
    assert details["skipped"][0]["reason"] == "explicit_url_required"


def test_explicit_request_directories_override_catalog_selection():
    orchestrator = SearchOrchestrator(registry=_runtime_registry())
    request = SearchRequest(
        keyword="traffic engineers",
        location="Phoenix, AZ",
        country="USA",
        directories=["bbb"],
    )

    assert orchestrator.get_directories(request) == ["bbb"]


def test_requested_unregistered_directory_is_not_executed():
    orchestrator = SearchOrchestrator(registry=_runtime_registry())
    request = SearchRequest(
        keyword="roofing contractors",
        location="Phoenix, AZ",
        country="USA",
        directories=["google_maps"],
    )

    assert orchestrator.build_targets({}, request) == []
    details = orchestrator.execution_details()
    assert details is not None
    assert details["skipped"][0]["reason"] == "provider_not_registered"


def test_service_list_supplies_query_when_keyword_is_empty():
    orchestrator = SearchOrchestrator(registry=_runtime_registry())
    request = SearchRequest(
        services=["traffic engineers"],
        location="Phoenix, AZ",
        country="USA",
        directories=["bbb"],
    )

    targets = orchestrator.build_targets({}, request)

    assert len(targets) == 1
    parameters = parse_qs(urlparse(targets[0]["url"]).query)
    assert parameters["find_text"] == ["traffic engineers"]


def test_explicit_target_has_precedence_over_generated_url():
    orchestrator = SearchOrchestrator(registry=_runtime_registry())
    request = SearchRequest(
        keyword="traffic engineers",
        location="Phoenix, AZ",
        country="USA",
    )

    targets = orchestrator.build_targets(
        {
            "directoryTargets": [
                {
                    "directory": "chambermaster",
                    "url": "https://example.com/chamber/list",
                }
            ]
        },
        request,
    )

    assert targets == [
        {
            "directory": "chambermaster",
            "url": "https://example.com/chamber/list",
        }
    ]


def test_generic_start_url_is_left_for_architecture_detection():
    orchestrator = SearchOrchestrator(registry=_runtime_registry())
    request = SearchRequest()

    targets = orchestrator.build_targets(
        {
            "mode": "embedded_js",
            "startUrls": [{"url": "https://example.com/directory"}],
        },
        request,
    )

    assert targets == []
    assert orchestrator.execution_details() == {
        "targets": [],
        "skipped": [],
    }
