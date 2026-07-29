from src.adapters.providers.request_builder import build_provider_request


def test_builds_standard_provider_request():
    request = build_provider_request(
        {
            "maxPages": 5,
            "maxListings": 25,
            "maxConcurrency": 2,
        },
        "chambermaster",
        "https://example.com/list",
        enable_website_enrichment=True,
        website_timeout_ms=12000,
    )

    assert request["directory"] == "chambermaster"
    assert request["input_data"]["architecture"] == "chambermaster"
    assert request["max_pages"] == 5
    assert request["max_companies"] == 25
    assert request["max_concurrency"] == 2
    assert request["enable_website_enrichment"] is True
    assert request["website_timeout_ms"] == 12000


def test_provider_settings_override_general_settings():
    request = build_provider_request(
        {
            "maxPages": 5,
            "providerSettings": {
                "bbb": {
                    "maxPages": 2,
                    "maxCompanies": 15,
                    "useApifyProxy": False,
                }
            },
        },
        "bbb",
        "https://www.bbb.org/search?find_text=engineers",
    )

    assert request["max_pages"] == 2
    assert request["max_companies"] == 15
    assert request["use_apify_proxy"] is False


def test_legacy_bbb_provider_settings_remain_supported():
    request = build_provider_request(
        {
            "bbbProvider": {
                "maxPages": 3,
                "maxCompanies": 20,
                "maxConcurrency": 4,
            }
        },
        "bbb",
        "https://www.bbb.org/search?find_text=engineers",
    )

    assert request["max_pages"] == 3
    assert request["max_companies"] == 20
    assert request["max_concurrency"] == 4
