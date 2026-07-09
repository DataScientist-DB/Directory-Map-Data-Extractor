from __future__ import annotations

import re
from typing import Any


class ServiceMatcher:
    """
    Matches requested services against all available company information.

    User value:
    Helps determine whether a company appears relevant to the
    user's requested service/product search.
    """

    SEARCH_FIELDS = (
        "company_name",
        "entity_name",
        "category_names",
        "service_names",
        "services",
        "description",
        "business_description",
        "website_title",
        "website_description",
        "meta_description",
        "schema_description",
        "title",
    )

    def match(
        self,
        record: dict[str, Any],
        requested_services: list[str] | str | None,
    ) -> tuple[bool, str, list[str]]:
        services = self._normalize_requested_services(requested_services)

        if not services:
            return False, "No Request", []

        text = self._record_text(record)

        matched: list[str] = []

        for service in services:
            if self._contains_service(text, service):
                matched.append(service)

        if not matched:
            return False, "No Match", []

        if len(matched) == len(services):
            return True, "Exact Match", matched

        return True, "Partial Match", matched

    def _normalize_requested_services(
        self,
        requested_services: list[str] | str | None,
    ) -> list[str]:
        if not requested_services:
            return []

        if isinstance(requested_services, str):
            requested_services = [requested_services]

        cleaned = []

        for service in requested_services:
            value = str(service).strip()

            if value:
                cleaned.append(value)

        return cleaned

    def _record_text(self, record: dict[str, Any]) -> str:
        parts = []

        for field in self.SEARCH_FIELDS:
            value = record.get(field)

            if isinstance(value, list):
                parts.extend(str(item) for item in value if item)

            elif value:
                parts.append(str(value))

        text = " ".join(parts).lower()
        text = re.sub(r"\s+", " ", text)

        return text

    def _contains_service(self, text: str, service: str) -> bool:
        service = service.strip().lower()

        if not service:
            return False

        # Exact phrase match
        if service in text:
            return True

        # Token-based fallback:
        # "traffic engineering" should match text containing both
        # "traffic" and "engineering" even if not adjacent.
        tokens = [
            token
            for token in re.split(r"[^a-z0-9]+", service)
            if len(token) >= 3
        ]

        if not tokens:
            return False

        return all(token in text for token in tokens)
