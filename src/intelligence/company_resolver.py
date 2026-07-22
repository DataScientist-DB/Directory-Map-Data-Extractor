from __future__ import annotations

import re
from copy import deepcopy
from typing import Any
from urllib.parse import urlparse


class CompanyResolver:
    """
    Detects and merges duplicate company records.

    Matching priority:
    1. Same normalized website domain
    2. Same normalized phone number
    3. Same company name and matching location

    The resolver is intentionally conservative to avoid merging
    unrelated companies with similar names.
    """

    def resolve(
        self,
        records: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], int]:
        resolved: list[dict[str, Any]] = []
        duplicates_merged = 0

        for source_record in records:
            record = deepcopy(source_record)
            match_index = self._find_match(resolved, record)

            if match_index is None:
                record["source_directories"] = self._source_directories(record)
                record["duplicate_count"] = 1
                resolved.append(record)
                continue

            resolved[match_index] = self._merge(
                resolved[match_index],
                record,
            )
            duplicates_merged += 1

        return resolved, duplicates_merged

    def _find_match(
        self,
        existing_records: list[dict[str, Any]],
        candidate: dict[str, Any],
    ) -> int | None:
        candidate_domain = self._website_domain(candidate)
        candidate_phone = self._normalize_phone(candidate.get("phone"))
        candidate_name = self._normalize_name(self._company_name(candidate))
        candidate_location = self._normalize_location(candidate)

        for index, existing in enumerate(existing_records):
            existing_domain = self._website_domain(existing)

            if (
                candidate_domain
                and existing_domain
                and candidate_domain == existing_domain
            ):
                return index

            existing_phone = self._normalize_phone(existing.get("phone"))

            if (
                candidate_phone
                and existing_phone
                and candidate_phone == existing_phone
            ):
                return index

            existing_name = self._normalize_name(
                self._company_name(existing)
            )
            existing_location = self._normalize_location(existing)

            if (
                candidate_name
                and existing_name
                and candidate_name == existing_name
                and candidate_location
                and existing_location
                and candidate_location == existing_location
            ):
                return index

        return None

    def _merge(
        self,
        primary: dict[str, Any],
        secondary: dict[str, Any],
    ) -> dict[str, Any]:
        merged = deepcopy(primary)

        for key, value in secondary.items():
            if self._is_empty(merged.get(key)) and not self._is_empty(value):
                merged[key] = value

        merged["source_directories"] = self._merge_unique_values(
            primary.get("source_directories"),
            secondary.get("source_directories")
            or self._source_directories(secondary),
        )

        merged["source_urls"] = self._merge_unique_values(
            primary.get("source_urls") or primary.get("source_url"),
            secondary.get("source_urls") or secondary.get("source_url"),
        )

        merged["profile_urls"] = self._merge_unique_values(
            primary.get("profile_urls") or primary.get("profile_url"),
            secondary.get("profile_urls") or secondary.get("profile_url"),
        )

        merged["duplicate_count"] = (
            int(primary.get("duplicate_count") or 1)
            + int(secondary.get("duplicate_count") or 1)
        )

        merged["email"] = self._prefer_value(
            primary.get("email"),
            secondary.get("email"),
        )

        merged["phone"] = self._prefer_value(
            primary.get("phone"),
            secondary.get("phone"),
        )

        merged["website"] = self._prefer_value(
            primary.get("website"),
            secondary.get("website"),
        )

        merged["category_names"] = self._merge_unique_values(
            primary.get("category_names"),
            secondary.get("category_names"),
        )

        merged["service_names"] = self._merge_unique_values(
            primary.get("service_names"),
            secondary.get("service_names"),
        )

        merged["products"] = self._merge_unique_values(
            primary.get("products"),
            secondary.get("products"),
        )

        merged["relevance_score"] = max(
            self._safe_int(primary.get("relevance_score")),
            self._safe_int(secondary.get("relevance_score")),
        )

        merged["business_intelligence_score"] = max(
            self._safe_int(
                primary.get("business_intelligence_score")
            ),
            self._safe_int(
                secondary.get("business_intelligence_score")
            ),
        )

        return merged

    def _company_name(self, record: dict[str, Any]) -> str:
        return str(
            record.get("entity_name")
            or record.get("company_name")
            or record.get("name")
            or ""
        )

    def _normalize_name(self, value: str) -> str:
        value = value.lower().strip()

        value = re.sub(
            r"\b(inc|incorporated|llc|ltd|limited|corp|corporation|company|co)\b",
            " ",
            value,
        )

        value = re.sub(r"[^a-z0-9]+", " ", value)
        return " ".join(value.split())

    def _website_domain(self, record: dict[str, Any]) -> str:
        website = str(record.get("website") or "").strip().lower()

        if not website:
            return ""

        if "://" not in website:
            website = "https://" + website

        try:
            domain = urlparse(website).netloc.lower()
        except ValueError:
            return ""

        if domain.startswith("www."):
            domain = domain[4:]

        return domain.split(":")[0]

    def _normalize_phone(self, value: Any) -> str:
        digits = re.sub(r"\D", "", str(value or ""))

        if len(digits) == 11 and digits.startswith("1"):
            digits = digits[1:]

        return digits if len(digits) >= 7 else ""

    def _normalize_location(
        self,
        record: dict[str, Any],
    ) -> str:
        parts = [
            record.get("city"),
            record.get("state"),
            record.get("postal_code"),
        ]

        text = " ".join(
            str(part)
            for part in parts
            if part
        ).lower()

        return " ".join(
            re.sub(r"[^a-z0-9]+", " ", text).split()
        )

    def _source_directories(
        self,
        record: dict[str, Any],
    ) -> list[str]:
        values = [
            record.get("architecture"),
            record.get("directory_name"),
            record.get("source_directory"),
        ]

        return self._merge_unique_values(values)

    def _merge_unique_values(
        self,
        *values: Any,
    ) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            if value is None:
                continue

            if isinstance(value, (list, tuple, set)):
                items = value
            else:
                items = re.split(r"[|,;]", str(value))

            for item in items:
                clean = str(item).strip()

                if not clean:
                    continue

                key = clean.lower()

                if key not in seen:
                    seen.add(key)
                    result.append(clean)

        return result

    def _prefer_value(
        self,
        first: Any,
        second: Any,
    ) -> Any:
        if not self._is_empty(first):
            return first

        return second

    def _is_empty(self, value: Any) -> bool:
        return value in (None, "", [], {}, ())

    def _safe_int(self, value: Any) -> int:
        try:
            return int(float(value or 0))
        except (TypeError, ValueError):
            return 0
