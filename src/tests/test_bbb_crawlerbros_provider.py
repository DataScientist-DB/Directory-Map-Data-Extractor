import pytest

from src.adapters.providers.bbb_crawlerbros import BBBCrawlerBrosProvider
from src.models.provider_report import ProviderReport
from src.models.provider_result import ProviderResult
from src.models.provider_status import ProviderStatus


class FakeAdapter:
    async def search(self, **kwargs):
        return ProviderResult(
            records=[{"entity_name": "ABC"}],
            report=ProviderReport(
                directory="bbb",
                provider="external",
                status=ProviderStatus.SUCCESS.value,
            ),
        )


@pytest.mark.asyncio
async def test_provider_returns_provider_result():
    provider = BBBCrawlerBrosProvider()

    provider._adapter = FakeAdapter()

    result = await provider.search(
        {"search_url": "https://bbb.org"}
    )

    assert isinstance(result, ProviderResult)
    assert result.report.status == ProviderStatus.SUCCESS.value
    assert len(result.records) == 1
