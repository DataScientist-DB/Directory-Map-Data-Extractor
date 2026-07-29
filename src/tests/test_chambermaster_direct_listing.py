from __future__ import annotations

from unittest.mock import AsyncMock, Mock

import pytest

from src.adapters.chambermaster import ChamberMasterAdapter


class _Page:
    def __init__(self, url: str) -> None:
        self.url = url


def _adapter(source_url: str) -> ChamberMasterAdapter:
    adapter = object.__new__(ChamberMasterAdapter)
    adapter.source_url = source_url
    adapter.debug = False
    adapter.stats = {
        "categories": 0,
        "categories_discovered": 0,
        "member_urls": 0,
        "profiles_processed": 0,
        "profiles_failed": 0,
    }
    return adapter


def test_direct_listing_detection_normalizes_query_and_trailing_slash():
    source_url = (
        "https://phoenixchamber.chambermaster.com/"
        "list/category/management-12027/?source=smoke"
    )
    adapter = _adapter(source_url)

    assert adapter._uses_direct_listing_source(
        source_url,
        [
            "https://phoenixchamber.chambermaster.com/"
            "list/category/management-12027"
        ],
    )


@pytest.mark.asyncio
async def test_crawl_honors_direct_category_without_request_filtering():
    category_url = (
        "https://phoenixchamber.chambermaster.com/"
        "list/category/management-12027"
    )
    adapter = _adapter(category_url)
    page = _Page(category_url)

    adapter.discover_categories = AsyncMock(
        return_value=[category_url]
    )
    adapter._filter_categories_by_request = Mock(
        side_effect=AssertionError(
            "Direct category URL must not be filtered by request text."
        )
    )
    adapter.discover_member_urls = AsyncMock(return_value=[])

    records = await adapter.crawl(page, max_records=3)

    assert records == []
    adapter.discover_member_urls.assert_awaited_once_with(
        page,
        [category_url],
    )
    assert adapter.stats["categories"] == 1


@pytest.mark.asyncio
async def test_crawl_still_filters_categories_discovered_from_landing_page():
    landing_url = "https://phoenixchamber.chambermaster.com/list"
    management_url = (
        "https://phoenixchamber.chambermaster.com/"
        "list/category/management-12027"
    )
    legal_url = (
        "https://phoenixchamber.chambermaster.com/"
        "list/category/legal-services-12028"
    )
    adapter = _adapter(landing_url)
    page = _Page(landing_url)

    adapter.discover_categories = AsyncMock(
        return_value=[management_url, legal_url]
    )
    adapter._filter_categories_by_request = Mock(
        return_value=[management_url]
    )
    adapter.discover_member_urls = AsyncMock(return_value=[])

    records = await adapter.crawl(page, max_records=3)

    assert records == []
    adapter._filter_categories_by_request.assert_called_once_with(
        [management_url, legal_url]
    )
    adapter.discover_member_urls.assert_awaited_once_with(
        page,
        [management_url],
    )
    assert adapter.stats["categories"] == 1
