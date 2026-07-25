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
