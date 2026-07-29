from __future__ import annotations

from typing import Any, Mapping

from src.adapters.providers.registry import ProviderRegistry
from src.discovery.directory_catalog import get_directory_by_id
from src.discovery.directory_request_builder import (
    DirectoryExecutionPlan,
    DirectoryTarget,
    SkippedDirectory,
    build_generated_target,
)
from src.discovery.directory_selector import (
    DirectorySelection,
    DirectorySelector,
)
from src.discovery.search_plan import build_search_plan


class SearchOrchestrator:
    """Select directories and build safe executable search targets."""

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
        self.last_execution_plan: DirectoryExecutionPlan | None = None

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

    def build_execution_plan(
        self,
        input_data: dict[str, Any],
        request: Any,
    ) -> DirectoryExecutionPlan:
        """
        Build targets using strict precedence:

        1. directoryTargets
        2. explicit architecture plus startUrls
        3. legacy first selected directory plus first startUrl
        4. verified catalog URL-generation strategies
        """
        explicit = self._explicit_targets(input_data)
        if explicit:
            return self._save_plan(
                DirectoryExecutionPlan(
                    targets=self._deduplicate_targets(explicit)
                )
            )

        architecture = str(
            input_data.get("architecture") or ""
        ).strip().lower()
        start_urls = self._start_urls(input_data)

        if (
            architecture
            and architecture not in {"auto", "unknown"}
            and start_urls
        ):
            return self._save_plan(
                DirectoryExecutionPlan(
                    targets=self._deduplicate_targets(
                        [
                            DirectoryTarget(
                                directory=architecture,
                                url=url,
                                origin="architecture_start_url",
                            )
                            for url in start_urls
                        ]
                    )
                )
            )

        selected_ids = self.get_directories(request)
        selection = self.selector.last_selection

        requested_ids = self._requested_directories(request)
        if requested_ids:
            selected_ids = requested_ids

        if requested_ids and start_urls:
            return self._save_plan(
                DirectoryExecutionPlan(
                    targets=[
                        DirectoryTarget(
                            directory=requested_ids[0],
                            url=start_urls[0],
                            origin="legacy_start_url",
                        )
                    ]
                )
            )

        if start_urls:
            return self._save_plan(DirectoryExecutionPlan())

        query = selection.query if selection else ""
        location = selection.location if selection else ""
        country = selection.country if selection else None
        targets: list[DirectoryTarget] = []
        skipped: list[SkippedDirectory] = []

        for directory in selected_ids:
            source = get_directory_by_id(directory)
            if source is None:
                skipped.append(
                    SkippedDirectory(
                        directory=directory,
                        reason="catalog_entry_not_found",
                        detail=(
                            "The requested directory is not present in "
                            "DIRECTORY_CATALOG."
                        ),
                    )
                )
                continue

            if (
                self.registry is not None
                and not self.registry.has_directory(directory)
            ):
                skipped.append(
                    SkippedDirectory(
                        directory=directory,
                        reason="provider_not_registered",
                        detail=(
                            "No enabled runtime provider is registered "
                            "for this directory."
                        ),
                    )
                )
                continue

            outcome = build_generated_target(
                source,
                query=query,
                location=location,
                country=country,
            )
            if isinstance(outcome, DirectoryTarget):
                targets.append(outcome)
            else:
                skipped.append(outcome)

        return self._save_plan(
            DirectoryExecutionPlan(
                targets=self._deduplicate_targets(targets),
                skipped=skipped,
            )
        )

    def build_targets(
        self,
        input_data: dict[str, Any],
        request: Any,
    ) -> list[dict[str, str]]:
        """Backward-compatible target list containing only directory and URL."""
        plan = self.build_execution_plan(input_data, request)
        return [
            target.to_dict(include_origin=False)
            for target in plan.targets
        ]

    def execution_details(self) -> dict[str, Any] | None:
        return (
            self.last_execution_plan.to_dict()
            if self.last_execution_plan is not None
            else None
        )

    def resolve_provider(self, directory: str):
        if self.registry is None:
            raise RuntimeError(
                "Provider resolution requires a ProviderRegistry."
            )
        return self.registry.select_for_directory(directory)

    def _save_plan(
        self,
        plan: DirectoryExecutionPlan,
    ) -> DirectoryExecutionPlan:
        self.last_execution_plan = plan
        return plan

    @staticmethod
    def _requested_directories(request: Any) -> list[str]:
        raw = (
            request.get("directories")
            if isinstance(request, Mapping)
            else getattr(request, "directories", None)
        )
        if isinstance(raw, str):
            values = [raw]
        else:
            values = list(raw or [])

        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized = str(value or "").strip().casefold()
            if normalized and normalized not in seen:
                seen.add(normalized)
                result.append(normalized)
        return result

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
    ) -> list[DirectoryTarget]:
        result: list[DirectoryTarget] = []
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
                result.append(
                    DirectoryTarget(
                        directory=directory,
                        url=url,
                        origin="directory_target",
                    )
                )
        return result

    @staticmethod
    def _deduplicate_targets(
        targets: list[DirectoryTarget],
    ) -> list[DirectoryTarget]:
        result: list[DirectoryTarget] = []
        seen: set[tuple[str, str]] = set()
        for target in targets:
            key = (
                target.directory.strip().casefold(),
                target.url.rstrip("/").casefold(),
            )
            if key not in seen:
                seen.add(key)
                result.append(target)
        return result
