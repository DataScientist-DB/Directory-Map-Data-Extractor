from __future__ import annotations

from typing import Any

from src.discovery.directory_catalog import DirectorySource
from src.discovery.directory_selector import DirectorySelection


def _source_item(source: DirectorySource) -> dict[str, Any]:
    return {
        "source_id": source.source_id,
        "name": source.name,
        "provider": source.provider,
        "source_type": source.source_type,
        "specialization": source.specialization,
        "priority": source.priority,
        "implemented": source.implemented,
    }


def build_search_plan(selection: DirectorySelection) -> dict[str, Any]:
    """Build a serializable and operationally transparent search plan."""
    selected = [_source_item(source) for source in selection.selected]
    unavailable = [
        {
            **_source_item(source),
            "reason": source.notes
            or "No executable provider is currently registered.",
        }
        for source in selection.recommended_but_unavailable
    ]

    return {
        "query": selection.query,
        "location": selection.location,
        "country": selection.country,
        "sector": selection.classification.sector,
        "industry": selection.classification.industry,
        "request_type": selection.classification.request_type,
        "industry_confidence": selection.classification.confidence,
        "matched_industry_term": selection.classification.matched_term,
        "directories_selected": selected,
        "general_directories_selected": [
            item
            for item, source in zip(selected, selection.selected)
            if source.is_general
        ],
        "specialized_directories_selected": [
            item
            for item, source in zip(selected, selection.selected)
            if source.is_specialized
        ],
        "recommended_directories_not_available": unavailable,
        "specialized_directories_not_available": [
            item
            for item, source in zip(
                unavailable,
                selection.recommended_but_unavailable,
            )
            if source.is_specialized
        ],
    }
