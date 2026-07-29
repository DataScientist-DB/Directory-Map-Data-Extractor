from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


def build_provider_input(
    source_input: Mapping[str, Any],
    directory: str,
    search_url: str,
) -> dict[str, Any]:
    """
    Build a provider-specific crawler input.

    All providers use the same input structure while differing only in
    directory name and starting URL.
    """

    target_input = deepcopy(dict(source_input))

    target_input["architecture"] = directory
    target_input["startUrls"] = [{"url": search_url}]

    search = dict(target_input.get("search") or {})
    search["directories"] = [directory]
    search["autoSelectDirectories"] = False

    target_input["search"] = search

    return target_input


def build_provider_request(
    source_input: Mapping[str, Any],
    directory: str,
    search_url: str,
    *,
    enable_website_enrichment: bool = False,
    website_timeout_ms: int = 15000,
) -> dict[str, Any]:
    """
    Build the standard request accepted by directory providers.

    Provider-specific options are read from ``providerSettings[directory]``.
    The legacy ``bbbProvider`` block remains supported during migration.
    """
    normalized_directory = str(directory or "").strip().casefold()
    target_input = build_provider_input(
        source_input,
        normalized_directory,
        search_url,
    )

    provider_settings = source_input.get("providerSettings") or {}
    if not isinstance(provider_settings, Mapping):
        raise ValueError("Input field 'providerSettings' must be an object.")

    settings = provider_settings.get(normalized_directory) or {}
    if not isinstance(settings, Mapping):
        raise ValueError(
            "Provider settings for "
            f"'{normalized_directory}' must be an object."
        )

    # Backward compatibility for the existing public BBB input contract.
    if normalized_directory == "bbb":
        legacy_settings = source_input.get("bbbProvider") or {}
        if not isinstance(legacy_settings, Mapping):
            raise ValueError("Input field 'bbbProvider' must be an object.")
        settings = {**legacy_settings, **settings}

    return {
        "input_data": target_input,
        "directory": normalized_directory,
        "search_url": str(search_url or "").strip(),
        "enable_website_enrichment": enable_website_enrichment,
        "website_timeout_ms": int(website_timeout_ms),
        "max_pages": int(
            settings.get(
                "maxPages",
                source_input.get("maxPages", 10),
            )
        ),
        "max_companies": int(
            settings.get(
                "maxCompanies",
                source_input.get("maxListings", 100),
            )
        ),
        "max_concurrency": int(
            settings.get(
                "maxConcurrency",
                source_input.get("maxConcurrency", 1),
            )
        ),
        "use_apify_proxy": bool(
            settings.get("useApifyProxy", True)
        ),
    }
