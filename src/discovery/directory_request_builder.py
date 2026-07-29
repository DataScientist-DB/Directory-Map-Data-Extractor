from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlencode

from src.discovery.directory_catalog import DirectorySource


@dataclass(frozen=True)
class DirectoryTarget:
    """One executable directory search target."""

    directory: str
    url: str
    origin: str = "generated"

    def to_dict(self, *, include_origin: bool = True) -> dict[str, str]:
        result = {
            "directory": self.directory,
            "url": self.url,
        }
        if include_origin:
            result["origin"] = self.origin
        return result


@dataclass(frozen=True)
class SkippedDirectory:
    """A selected source that cannot become an executable target."""

    directory: str
    reason: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {
            "directory": self.directory,
            "reason": self.reason,
            "detail": self.detail,
        }


@dataclass
class DirectoryExecutionPlan:
    """Targets and transparent skip decisions for one search."""

    targets: list[DirectoryTarget] = field(default_factory=list)
    skipped: list[SkippedDirectory] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "targets": [target.to_dict() for target in self.targets],
            "skipped": [item.to_dict() for item in self.skipped],
        }


def build_bbb_search_url(
    *,
    query: str,
    location: str,
    country: str | None,
) -> str | None:
    """Create a deterministic BBB keyword/location search URL."""
    clean_query = query.strip()
    clean_location = location.strip()

    if not clean_query:
        return None

    parameters = {
        "find_country": (country or "USA").strip() or "USA",
        "find_text": clean_query,
    }
    if clean_location:
        parameters["find_loc"] = clean_location

    return "https://www.bbb.org/search?" + urlencode(parameters)


def build_generated_target(
    source: DirectorySource,
    *,
    query: str,
    location: str,
    country: str | None,
) -> DirectoryTarget | SkippedDirectory:
    """
    Convert a selected catalog source into an executable target.

    Only strategies known to be supported by this codebase are generated.
    Directory homepages are never used as fake search-result URLs.
    """
    if source.source_id == "bbb":
        url = build_bbb_search_url(
            query=query,
            location=location,
            country=country,
        )
        if url:
            return DirectoryTarget(
                directory=source.source_id,
                url=url,
            )
        return SkippedDirectory(
            directory=source.source_id,
            reason="query_required",
            detail="BBB URL generation requires a keyword or service.",
        )

    if source.source_id == "chambermaster":
        return SkippedDirectory(
            directory=source.source_id,
            reason="explicit_url_required",
            detail=(
                "ChamberMaster searches require a chamber-specific "
                "directory URL in directoryTargets or startUrls."
            ),
        )

    return SkippedDirectory(
        directory=source.source_id,
        reason="url_strategy_not_implemented",
        detail=(
            "No verified search-URL strategy is implemented for "
            f"{source.name}."
        ),
    )
