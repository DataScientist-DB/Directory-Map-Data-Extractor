import pytest

from src.intelligence.company_processing_pipeline import (
    CompanyProcessingPipeline,
)


@pytest.mark.asyncio
async def test_normalizes_scores_and_qualifies_company():
    pipeline = CompanyProcessingPipeline(
        request={
            "services": ["traffic engineers"],
            "location": "Phoenix, AZ",
        }
    )

    result = await pipeline.process(
        {
            "name": "Phoenix Traffic Engineers",
            "services": "traffic engineers",
            "city": "Phoenix",
            "state": "AZ",
            "website": "https://example.com",
            "email": "info@example.com",
            "phone": "+1 602 555 0100",
        }
    )

    assert result is not None
    assert result["entity_name"] == "Phoenix Traffic Engineers"
    assert result["company_name"] == "Phoenix Traffic Engineers"
    assert result["business_intelligence_score"] == 60
    assert result["intelligence_score"] == 60
    assert result["contact_ready"] is True
    assert result["relevance_score"] > 0
    assert result["processing_status"] == "processed"
    assert result["processing_pipeline_version"] == "1.0"


class FakeWebsiteEnricher:
    def __init__(self) -> None:
        self.calls = 0

    async def enrich_record_from_website(
        self,
        page,
        record,
        timeout_ms,
    ):
        self.calls += 1
        record["email"] = "contact@example.com"
        record["linkedin"] = "https://linkedin.com/company/example"
        record["website_enrichment_status"] = "success"
        return record


@pytest.mark.asyncio
async def test_uses_website_enrichment_when_browser_page_is_available():
    enricher = FakeWebsiteEnricher()
    pipeline = CompanyProcessingPipeline(
        enable_website_enrichment=True,
        website_enricher=enricher,
    )

    result = await pipeline.process(
        {
            "entity_name": "Example Company",
            "website": "https://example.com",
        },
        page=object(),
    )

    assert result is not None
    assert enricher.calls == 1
    assert result["email"] == "contact@example.com"
    assert result["business_intelligence_score"] == 50


@pytest.mark.asyncio
async def test_marks_enrichment_deferred_without_browser_page():
    pipeline = CompanyProcessingPipeline(
        enable_website_enrichment=True,
    )

    result = await pipeline.process(
        {
            "entity_name": "Structured Provider Company",
            "website": "https://example.com",
        }
    )

    assert result is not None
    assert (
        result["website_enrichment_status"]
        == "deferred_no_browser"
    )


@pytest.mark.asyncio
async def test_diagnostic_record_is_not_processed_as_company():
    pipeline = CompanyProcessingPipeline()

    result = await pipeline.process(
        {
            "entity_name": "ACCESS DIAGNOSTIC",
            "status": "blocked",
            "blocked_reason": "Cloudflare Turnstile",
        }
    )

    assert result is None


@pytest.mark.asyncio
async def test_process_many_filters_non_company_records():
    pipeline = CompanyProcessingPipeline()

    results = await pipeline.process_many(
        [
            {"name": "Company A", "phone": "123"},
            {"status": "failed", "reason": "test"},
            {"website": "https://missing-name.example"},
        ]
    )

    assert len(results) == 1
    assert results[0]["entity_name"] == "Company A"
