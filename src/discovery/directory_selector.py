from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from src.discovery.directory_catalog import (
    DIRECTORY_CATALOG,
    DirectorySource,
)
from src.discovery.industry_classifier import (
    IndustryClassification,
    classify_industry,
)


@dataclass(frozen=True)
class DirectorySelection:
    """Immutable directory-selection result for one search request."""

    query: str
    location: str
    country: str | None
    classification: IndustryClassification
    selected: tuple[DirectorySource, ...]
    recommended_but_unavailable: tuple[DirectorySource, ...] = ()

    @property
    def general_sources(self) -> tuple[DirectorySource, ...]:
        return tuple(source for source in self.selected if source.is_general)

    @property
    def specialized_sources(self) -> tuple[DirectorySource, ...]:
        return tuple(
            source for source in self.selected if source.is_specialized
        )

    @property
    def unavailable_specialized_sources(
        self,
    ) -> tuple[DirectorySource, ...]:
        return tuple(
            source
            for source in self.recommended_but_unavailable
            if source.is_specialized
        )

    @property
    def provider_ids(self) -> tuple[str, ...]:
        return tuple(source.provider for source in self.selected)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "location": self.location,
            "country": self.country,
            "sector": self.classification.sector,
            "industry": self.classification.industry,
            "request_type": self.classification.request_type,
            "industry_confidence": self.classification.confidence,
            "matched_industry_term": self.classification.matched_term,
            "selected_directories": [
                source.source_id for source in self.selected
            ],
            "selected_providers": list(self.provider_ids),
            "general_directories": [
                source.source_id for source in self.general_sources
            ],
            "specialized_directories": [
                source.source_id for source in self.specialized_sources
            ],
            "recommended_directories_not_available": [
                source.source_id
                for source in self.recommended_but_unavailable
            ],
            "specialized_directories_not_available": [
                source.source_id
                for source in self.unavailable_specialized_sources
            ],
        }


def _read_value(request: Any, *names: str) -> Any:
    for name in names:
        value = (
            request.get(name)
            if isinstance(request, dict)
            else getattr(request, name, None)
        )
        if value not in (None, "", [], ()):
            return value
    return None


def _request_query(request: Any) -> str:
    value = _read_value(
        request,
        "keyword",
        "query",
        "service",
        "service_name",
        "product",
        "product_name",
        "category",
    )
    return str(value or "").strip()


def _request_location(request: Any) -> str:
    value = _read_value(request, "location", "city", "region", "state")
    return str(value or "").strip()


def _request_country(request: Any) -> str | None:
    value = _read_value(request, "country", "country_code")
    text = str(value or "").strip()
    return text or None


def _rank(source: DirectorySource) -> tuple[int, float, float, str]:
    return (
        -source.priority,
        -source.estimated_quality,
        -source.estimated_speed,
        source.source_id,
    )


def _limit(
    sources: Iterable[DirectorySource],
    maximum: int | None,
) -> tuple[DirectorySource, ...]:
    values = tuple(sources)
    if maximum is None:
        return values
    return values[:max(0, maximum)]


def select_directories(
    *,
    query: str,
    location: str,
    country: str | None = None,
    implemented_only: bool = False,
    max_general_sources: int | None = None,
    max_specialized_sources: int | None = None,
    catalog: Sequence[DirectorySource] = DIRECTORY_CATALOG,
    available_provider_ids: Iterable[str] | None = None,
) -> DirectorySelection:
    """
    Select general and industry-specific sources using catalog metadata.

    ``implemented_only=False`` is useful for planning and recommendations.
    ``implemented_only=True`` produces an executable selection and moves
    relevant unavailable sources into ``recommended_but_unavailable``.
    When ``available_provider_ids`` is supplied, catalog implementation flags
    and runtime registration must both agree before a source is executable.
    """
    classification = classify_industry(query)
    runtime_ids = (
        {value.strip().casefold() for value in available_provider_ids}
        if available_provider_ids is not None
        else None
    )

    general: list[DirectorySource] = []
    specialized: list[DirectorySource] = []

    for source in catalog:
        if not source.enabled or not source.supports_country(country):
            continue
        if source.is_general:
            general.append(source)
        elif source.supports_industry(classification.industry):
            specialized.append(source)

    general.sort(key=_rank)
    specialized.sort(key=_rank)

    relevant = (
        *_limit(general, max_general_sources),
        *_limit(specialized, max_specialized_sources),
    )

    if not implemented_only:
        return DirectorySelection(
            query=query,
            location=location,
            country=country,
            classification=classification,
            selected=relevant,
        )

    def executable(source: DirectorySource) -> bool:
        if not source.implemented:
            return False
        if runtime_ids is None:
            return True
        return (
            source.provider.casefold() in runtime_ids
            or source.source_id.casefold() in runtime_ids
        )

    return DirectorySelection(
        query=query,
        location=location,
        country=country,
        classification=classification,
        selected=tuple(source for source in relevant if executable(source)),
        recommended_but_unavailable=tuple(
            source for source in relevant if not executable(source)
        ),
    )


class DirectorySelector:
    """
    Catalog-backed selector with both current and legacy call interfaces.

    Keyword calls return ``DirectorySelection``:
        selector.select(query="roofing", location="Phoenix", country="USA")

    The legacy positional request call returns executable provider IDs:
        selector.select(request)
    """

    def __init__(
        self,
        *,
        max_general_sources: int | None = None,
        max_specialized_sources: int | None = None,
        implemented_only: bool = False,
        catalog: Sequence[DirectorySource] = DIRECTORY_CATALOG,
        available_provider_ids: Iterable[str] | None = None,
    ) -> None:
        self.max_general_sources = max_general_sources
        self.max_specialized_sources = max_specialized_sources
        self.implemented_only = implemented_only
        self.catalog = catalog
        self.available_provider_ids = (
            tuple(available_provider_ids)
            if available_provider_ids is not None
            else None
        )
        self.last_selection: DirectorySelection | None = None

    def _select(
        self,
        *,
        query: str,
        location: str,
        country: str | None,
        implemented_only: bool | None = None,
    ) -> DirectorySelection:
        self.last_selection = select_directories(
            query=query,
            location=location,
            country=country,
            implemented_only=(
                self.implemented_only
                if implemented_only is None
                else implemented_only
            ),
            max_general_sources=self.max_general_sources,
            max_specialized_sources=self.max_specialized_sources,
            catalog=self.catalog,
            available_provider_ids=self.available_provider_ids,
        )
        return self.last_selection

    def select(
        self,
        request: Any | None = None,
        *,
        query: str | None = None,
        location: str | None = None,
        country: str | None = None,
        implemented_only: bool | None = None,
    ) -> DirectorySelection | list[str]:
        if request is not None:
            selection = self._select(
                query=_request_query(request),
                location=_request_location(request),
                country=_request_country(request),
                implemented_only=(
                    True if implemented_only is None else implemented_only
                ),
            )
            return list(selection.provider_ids)

        return self._select(
            query=str(query or "").strip(),
            location=str(location or "").strip(),
            country=country,
            implemented_only=implemented_only,
        )

    def selection_details(
        self,
        request: Any | None = None,
        *,
        query: str | None = None,
        location: str | None = None,
        country: str | None = None,
        implemented_only: bool | None = None,
    ) -> dict[str, Any] | None:
        if request is not None:
            self.select(request, implemented_only=implemented_only)
        elif query is not None or location is not None or country is not None:
            self.select(
                query=query,
                location=location,
                country=country,
                implemented_only=implemented_only,
            )

        return (
            self.last_selection.to_dict()
            if self.last_selection is not None
            else None
        )
