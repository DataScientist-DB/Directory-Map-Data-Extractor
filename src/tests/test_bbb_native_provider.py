from typing import Any

import pytest

from src.adapters.providers.bbb_native import BBBNativeProvider
from src.models.provider_result import ProviderResult
from src.models.provider_status import ProviderStatus


@pytest.mark.asyncio
async def test_native_provider_preserves_blocked_status() -> None:
    async def fake_crawler(
        input_data: dict[str, Any],
        *,
        enable_website_enrichment: bool = False,
        website_timeout_ms: int = 15000,
    ) -> dict[str, Any]:
        return {
            "status": "adapter_extraction_complete",
            "access_status": "blocked",
            "blocked_reason": "Cloudflare Turnstile",
            "access_reason": "Cloudflare Turnstile",
            "records_found": 0,
            "access_http_status": 403,
            "access_pages_visited": 1,
            "access_profiles_found": 0,
            "access_recommendation": "Use Apify Residential Proxy.",
        }

    provider = BBBNativeProvider(crawler=fake_crawler)

    result = await provider.search(
        {
            "input_data": {
                "mode": "auto",
                "search": {
                    "directories": ["bbb"],
                },
            },
            "search_url": (
                "https://www.bbb.org/us/ca/"
                "costa-mesa/category/traffic-engineers"
            ),
        }
    )

    assert isinstance(result, ProviderResult)
    assert result.report.status == ProviderStatus.BLOCKED.value
    assert result.report.reason == "Cloudflare Turnstile"
    assert result.records == []
    assert result.should_fallback is True
    assert provider.health() == "blocked"
    assert result.report.metadata["http_status"] == 403
