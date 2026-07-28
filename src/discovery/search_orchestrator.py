from __future__ import annotations

from typing import Any, Mapping

from src.adapters.providers.registry import ProviderRegistry
from src.discovery.directory_selector import (
    DirectorySelection,
    DirectorySelector,
)
from src.discovery.search_plan import build_search_plan


class SearchOrchestrator:
    """Build executable, backward-compatible directory targets."""

    def __init__(
        self,
        *,
        registry: ProviderRegistry | None = None,
        selector: DirectorySelector | None = None,
    ) -> None:
        self.registry = registry
        available = (
            registry.directory_names()
            if registry is not None
            else None
        )
        self.selector = selector or DirectorySelector(
            implemented_only=True,
            available_provider_ids=available,
        )

    def get_directories(self, request: Any) -> list[str]:
        result = self.selector.select(request)
        if isinstance(result, DirectorySelection):
            return list(result.provider_ids)
        return result

    def get_search_plan(self, request: Any) -> dict[str, Any]:
        self.get_directories(request)
        selection = self.selector.last_selection
        if selection is None:
            raise RuntimeError("Directory selection did not produce a result.")
        return build_search_plan(selection)

    def build_targets(
        self,
        input_data: dict[str, Any],
        request: Any,
    ) -> list[dict[str, str]]:
        explicit = self._explicit_targets(input_data)
        if explicit:
            return self._deduplicate_targets(explicit)

        architecture = str(
            input_data.get("architecture") or ""
        ).strip().lower()
        start_urls = self._start_urls(input_data)

        if (
            architecture
            and architecture not in {"auto", "unknown"}
            and start_urls
        ):
            return self._deduplicate_targets(
                [
                    {"directory": architecture, "url": url}
                    for url in start_urls
                ]
            )

        selected = self.get_directories(request)

        # A supplied URL historically represents one directory page. Preserve
        # that behavior instead of assigning the same URL to unrelated sources.
        if selected and start_urls:
            return [
                {
                    "directory": selected[0],
                    "url": start_urls[0],
                }
            ]

        # Catalog selection cannot invent directory-specific search URLs.
        # URL construction belongs in the provider/request-builder layer.
        return []

    def resolve_provider(self, directory: str):
        """Resolve a target directory to its best registered provider."""
        if self.registry is None:
            raise RuntimeError(
                "Provider resolution requires a ProviderRegistry."
            )
        return self.registry.select_for_directory(directory)

    @staticmethod
    def _start_urls(input_data: Mapping[str, Any]) -> list[str]:
        result: list[str] = []
        for item in input_data.get("startUrls") or []:
            if isinstance(item, str):
                url = item.strip()
            elif isinstance(item, Mapping):
                url = str(item.get("url") or "").strip()
            else:
                continue
            if url:
                result.append(url)
        return result

    @staticmethod
    def _explicit_targets(
        input_data: Mapping[str, Any],
    ) -> list[dict[str, str]]:
        result: list[dict[str, str]] = []
        for target in input_data.get("directoryTargets") or []:
            if not isinstance(target, Mapping):
                continue
            directory = str(
                target.get("directory")
                or target.get("architecture")
                or ""
            ).strip().lower()
            url = str(target.get("url") or "").strip()
            if directory and url:
                result.append({"directory": directory, "url": url})
        return result

    @staticmethod
    def _deduplicate_targets(
        targets: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        result: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for target in targets:
            key = (
                target["directory"].strip().casefold(),
                target["url"].rstrip("/").casefold(),
            )
            if key not in seen:
                seen.add(key)
                result.append(target)
        return result
