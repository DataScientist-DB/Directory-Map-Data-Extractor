from src.discovery.search_orchestrator import SearchOrchestrator
from src.models.search_request import SearchRequest


def test_builds_multiple_explicit_targets():
    request = SearchRequest(
        directories=["chambermaster", "bbb"],
    )

    input_data = {
        "directoryTargets": [
            {
                "directory": "chambermaster",
                "url": "https://example.com/chamber/list",
            },
            {
                "directory": "bbb",
                "url": "https://example.com/bbb/search",
            },
        ]
    }

    targets = SearchOrchestrator().build_targets(
        input_data=input_data,
        request=request,
    )

    assert len(targets) == 2
    assert targets[0]["directory"] == "chambermaster"
    assert targets[1]["directory"] == "bbb"


def test_removes_duplicate_targets():
    request = SearchRequest(
        directories=["chambermaster"],
    )

    input_data = {
        "directoryTargets": [
            {
                "directory": "chambermaster",
                "url": "https://example.com/list",
            },
            {
                "directory": "chambermaster",
                "url": "https://example.com/list/",
            },
        ]
    }

    targets = SearchOrchestrator().build_targets(
        input_data=input_data,
        request=request,
    )

    assert len(targets) == 1
