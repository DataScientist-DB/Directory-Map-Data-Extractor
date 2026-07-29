from __future__ import annotations

from typing import Any, Iterable

from src.enrichment.website_enricher import WebsiteEnricher
from src.intelligence.company_qualifier import CompanyQualifier
from src.intelligence.intelligence_score import IntelligenceScore


DIAGNOSTIC_STATUSES = {
    "blocked",
    "failed",
    "runtime_error",
    "authentication_failed",
    "rate_limited",
    "rental_required",
    "actor_unavailable",
    "input_error",
    "demo",
    "timeout",
    "network_error",
    "not_supported",
    "architecture_detected",
}


class CompanyProcessingPipeline:
    """
    Normalize, enrich, score, and qualify discovered company records.

    The pipeline is independent of providers and dataset storage. Callers may
    use it for native crawler records or structured provider results.
    """

    VERSION = "1.0"

    def __init__(
        self,
        *,
        request: dict[str, Any] | None = None,
        enable_website_enrichment: bool = False,
        website_timeout_ms: int = 15000,
        website_enricher: WebsiteEnricher | None = None,
        qualifier: CompanyQualifier | None = None,
        intelligence: IntelligenceScore | None = None,
    ) -> None:
        self.request = dict(request or {})
        self.enable_website_enrichment = enable_website_enrichment
        self.website_timeout_ms = int(website_timeout_ms)
        self.website_enricher = website_enricher or WebsiteEnricher()
        self.qualifier = qualifier or CompanyQualifier()
        self.intelligence = intelligence or IntelligenceScore()

    async def process(
        self,
        record: dict[str, Any],
        *,
        page: Any | None = None,
    ) -> dict[str, Any] | None:
        """Return one processed company record, or None when not a company."""
        if not isinstance(record, dict):
            return None

        normalized = self._normalize(record)

        if self._is_diagnostic(normalized):
            return None

        if not normalized.get("entity_name"):
            return None

        if (
            self.enable_website_enrichment
            and normalized.get("website")
            and page is not None
        ):
            normalized = (
                await self.website_enricher.enrich_record_from_website(
                    page,
                    normalized,
                    timeout_ms=self.website_timeout_ms,
                )
            )
        elif (
            self.enable_website_enrichment
            and normalized.get("website")
            and page is None
        ):
            normalized.setdefault(
                "website_enrichment_status",
                "deferred_no_browser",
            )
            normalized.setdefault("website_enrichment_error", "")

        score, grade = self.intelligence.score(normalized)
        normalized["business_intelligence_score"] = score
        normalized["business_intelligence_grade"] = grade
        normalized["intelligence_score"] = score
        normalized["intelligence_grade"] = grade

        normalized = self.qualifier.qualify(
            record=normalized,
            request=self.request,
        )

        normalized["processing_status"] = "processed"
        normalized["processing_pipeline_version"] = self.VERSION
        return normalized

    async def process_many(
        self,
        records: Iterable[dict[str, Any]],
        *,
        page: Any | None = None,
    ) -> list[dict[str, Any]]:
        processed: list[dict[str, Any]] = []

        for record in records:
            result = await self.process(record, page=page)
            if result is not None:
                processed.append(result)

        return processed

    @staticmethod
    def _normalize(record: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(record)

        entity_name = str(
            normalized.get("entity_name")
            or normalized.get("company_name")
            or normalized.get("name")
            or ""
        ).strip()

        if entity_name:
            normalized["entity_name"] = entity_name
            normalized.setdefault("company_name", entity_name)

        if not normalized.get("service_names_str"):
            service_value = (
                normalized.get("service_names")
                or normalized.get("services")
                or ""
            )
            normalized["service_names_str"] = (
                CompanyProcessingPipeline._join_values(service_value)
            )

        if not normalized.get("category_names_str"):
            category_value = (
                normalized.get("category_names")
                or normalized.get("categories")
                or ""
            )
            normalized["category_names_str"] = (
                CompanyProcessingPipeline._join_values(category_value)
            )

        normalized.setdefault("status", "success")
        normalized.setdefault("blocked_reason", "")
        return normalized

    @staticmethod
    def _join_values(value: Any) -> str:
        if isinstance(value, dict):
            values = value.values()
        elif isinstance(value, (list, tuple, set)):
            values = value
        else:
            return str(value or "").strip()

        return "; ".join(
            str(item).strip()
            for item in values
            if str(item).strip()
        )

    @staticmethod
    def _is_diagnostic(record: dict[str, Any]) -> bool:
        status = str(record.get("status") or "").strip().casefold()
        access_status = str(
            record.get("access_status") or ""
        ).strip().casefold()

        return bool(
            status in DIAGNOSTIC_STATUSES
            or access_status in DIAGNOSTIC_STATUSES
            or str(record.get("blocked_reason") or "").strip()
        )
