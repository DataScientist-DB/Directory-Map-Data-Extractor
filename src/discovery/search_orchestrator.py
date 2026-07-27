from __future__ import annotations

from typing import Any

from src.discovery.directory_selector import DirectorySelector


class SearchOrchestrator:
    """
    Builds executable directory targets for one user search request.

    RC1.7.2:
      - supports one or more explicitly configured directory URLs
      - keeps adapter execution sequential
      - allows one combined dataset/export
    """

    def __init__(self) -> None:
        self.selector = DirectorySelector()

    def get_directories(self, request: Any) -> list[str]:
        return self.selector.select(request)

    def build_targets(
        self,
        input_data: dict[str, Any],
        request: Any,
    ) -> list[dict[str, str]]:
        """
        Return targets such as:

        [
            {
                "directory": "chambermaster",
                "url": "https://www.costamesachamber.com/list"
            },
            {
                "directory": "bbb",
                "url": "https://www.bbb.org/..."
            }
        ]
        """

        explicit_targets = input_data.get("directoryTargets") or []

        targets: list[dict[str, str]] = []

        for target in explicit_targets:
            if not isinstance(target, dict):
                continue

            directory = str(
                target.get("directory")
                or target.get("architecture")
                or ""
            ).strip().lower()

            url = str(target.get("url") or "").strip()

            if directory and url:
                targets.append(
                    {
                        "directory": directory,
                        "url": url,
                    }
                )

        if targets:
            return self._deduplicate_targets(targets)
        if targets:
            return self._deduplicate_targets(targets)

        # NEW: Explicit architecture + startUrls support
        architecture = str(
            input_data.get("architecture") or ""
        ).strip().lower()

        start_urls = input_data.get("startUrls") or []

        if (
            architecture
            and architecture not in {"auto", "unknown"}
            and start_urls
        ):
            first_url = str(
                (start_urls[0] or {}).get("url") or ""
            ).strip()

            if first_url:
                return self._deduplicate_targets(
                    [
                        {
                            "directory": architecture,
                            "url": first_url,
                        }
                    ]
                )


        # Backward-compatible single-target mode
        selected = self.get_directories(request)
        start_urls = input_data.get("startUrls") or []

        if selected and start_urls:
            first_url = str(
                (start_urls[0] or {}).get("url") or ""
            ).strip()

            if first_url:
                targets.append(
                    {
                        "directory": selected[0],
                        "url": first_url,
                    }
                )

        return self._deduplicate_targets(targets)

    def _deduplicate_targets(
        self,
        targets: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        result: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()

        for target in targets:
            key = (
                target["directory"].lower(),
                target["url"].rstrip("/").lower(),
            )

            if key in seen:
                continue

            seen.add(key)
            result.append(target)

        return result
