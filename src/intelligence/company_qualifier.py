from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from src.intelligence.service_matcher import ServiceMatcher

@dataclass(slots=True)
class QualificationResult:
    qualification: str = "Needs Review"
    recommendation: str = "★★ Needs Review"

    contact_ready: bool = False

    service_match: bool = False
    product_match: bool = False

    location_match: bool = False
    location_match_level: str = "No Match"

    relevance_score: int = 0

    reasons: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)

class CompanyQualifier:
    """
    Practical company qualification engine.

    Goal:
    Help users decide which companies match their requested
    services/products/location and are ready to contact.
    """

    def __init__(self):
        self.service_matcher = ServiceMatcher()

    def qualify(
        self,
        record: dict[str, Any],
        request: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        request = request or {}

        result = QualificationResult()

        service_terms = self._terms(
            request.get("services")
            or request.get("keywords")
            or request.get("keyword")
        )

        product_terms = self._terms(
            request.get("products")
        )

        location_terms = self._terms(
            request.get("locations")
            or request.get("location")
        )

        service_match, service_level, matched_services = self.service_matcher.match(
            record=record,
            requested_services=service_terms,
        )

        result.service_match = service_match

        searchable_text = self._record_text(record)
        result.product_match = self._contains_any(searchable_text, product_terms)

        result.location_match_level = self._location_match_level(
            record,
            location_terms,
        )

        result.location_match = result.location_match_level != "No Match"

        result.contact_ready = bool(
            record.get("email")
            or record.get("phone")
            or record.get("website")
            or record.get("contact_page")
            or record.get("linkedin")
        )


        if result.service_match:
            result.reasons.append("Provides requested service or related business activity.")
        elif service_terms:
            result.missing.append("Requested service not clearly detected.")

        if result.product_match:
            result.reasons.append("Provides requested product or related product category.")
        elif product_terms:
            result.missing.append("Requested product not clearly detected.")

        if result.location_match:
            result.reasons.append("Matches requested location.")
        elif location_terms:
            result.missing.append("Requested location not confirmed.")

        if record.get("email"):
            result.reasons.append("Email available.")
        else:
            result.missing.append("Email missing.")

        if record.get("phone"):
            result.reasons.append("Phone available.")
        else:
            result.missing.append("Phone missing.")

        if record.get("website"):
            result.reasons.append("Website available.")
        else:
            result.missing.append("Website missing.")

        if record.get("linkedin"):
            result.reasons.append("LinkedIn available.")

        score = self._score(result)

        result.qualification, result.recommendation = self._label(score)

        record["qualification"] = result.qualification
        record["recommendation"] = result.recommendation
        record["contact_ready"] = result.contact_ready
        record["service_match"] = result.service_match
        record["product_match"] = result.product_match
        record["location_match"] = result.location_match
        record["location_match_level"] = result.location_match_level
        record["qualification_reasons"] = " | ".join(result.reasons)
        record["missing_information"] = " | ".join(result.missing)
        record["service_match_level"] = service_level
        record["matched_services"] = ", ".join(matched_services)

        result.relevance_score = self._relevance_score(
            result,
            record,
        )

        record["relevance_score"] = result.relevance_score


        record["service_match_level"] = service_level
        record["matched_services"] = ", ".join(matched_services)

        return record

    def _terms(self, value: Any) -> list[str]:
        if not value:
            return []

        if isinstance(value, str):
            return [value.strip().lower()] if value.strip() else []

        if isinstance(value, list):
            return [
                str(item).strip().lower()
                for item in value
                if str(item).strip()
            ]

        return [str(value).strip().lower()]

    def _record_text(self, record: dict[str, Any]) -> str:
        fields = [
            "company_name",
            "category_names",
            "categories",
            "service_names",
            "services",
            "product_names",
            "products",
            "description",
            "business_description",
            "website_title",
            "website_description",
            "schema_name",
        ]

        parts = []

        for field in fields:
            value = record.get(field)
            if value:
                parts.append(str(value))

        return " ".join(parts).lower()

    def _contains_any(self, text: str, terms: list[str]) -> bool:
        if not terms:
            return False

        return any(term in text for term in terms)

    def _location_match(
        self,
        record: dict[str, Any],
        location_terms: list[str],
    ) -> bool:
        """
        Flexible location matching.

        Examples:

        Request:
            Costa Mesa, CA

        Matches:

            Costa Mesa

            Costa Mesa CA

            Costa Mesa California

            CA

            California
        """

        if not location_terms:
            return False

        location_text = " ".join(
            str(record.get(field, ""))
            for field in (
                "address",
                "city",
                "state",
                "postal_code",
                "country",
                "location",
            )
        ).lower()

        # Normalize punctuation
        location_text = (
            location_text
            .replace(",", " ")
            .replace(";", " ")
        )

        request_tokens = []

        state_map = {
            "ca": "california",
            "ny": "new york",
            "tx": "texas",
            "fl": "florida",
            "wa": "washington",
            "or": "oregon",
            "az": "arizona",
            "nv": "nevada",
        }

        for term in location_terms:

            term = term.lower()

            parts = [
                p.strip()
                for p in term.split(",")
                if p.strip()
            ]

            for part in parts:

                request_tokens.append(part)

                if part in state_map:
                    request_tokens.append(state_map[part])

                for abbr, fullname in state_map.items():
                    if part == fullname:
                        request_tokens.append(abbr)

        request_tokens = list(dict.fromkeys(request_tokens))

        if not request_tokens:
            return False

        matched = 0

        for token in request_tokens:
            if token in location_text:
                matched += 1

        return matched > 0



    def _location_match_level(
        self,
        record: dict[str, Any],
        location_terms: list[str],
    ) -> str:
        if not location_terms:
            return "No Match"

        city = str(record.get("city", "")).lower()
        state = str(record.get("state", "")).lower()
        country = str(record.get("country", "")).lower()

        request_text = " ".join(location_terms).lower()

        normalized = (
            request_text
            .replace(",", " ")
            .replace(";", " ")
        )

        tokens = [
            item.strip()
            for item in normalized.split()
            if item.strip()
        ]

        state_map = {
            "ca": "california",
            "ny": "new york",
            "tx": "texas",
            "fl": "florida",
            "wa": "washington",
            "or": "oregon",
            "az": "arizona",
            "nv": "nevada",
        }

        expanded_tokens = set(tokens)

        for token in tokens:
            if token in state_map:
                expanded_tokens.add(state_map[token])

            for abbr, fullname in state_map.items():
                if token == fullname:
                    expanded_tokens.add(abbr)

        if city and city in request_text:
            return "City Match"

        if state and (
            state in expanded_tokens
            or state in request_text
        ):
            return "State Match"

        if country and country in request_text:
            return "Country Match"

        return "No Match"

    def _score(self, result: QualificationResult) -> int:
        score = 0

        if result.service_match:
            score += 35

        if result.product_match:
            score += 25

        if result.location_match:
            score += 15

        if result.contact_ready:
            score += 15

        if "Email available." in result.reasons:
            score += 5

        if "Phone available." in result.reasons:
            score += 5

        return min(score, 100)

    def _relevance_score(
        self,
        result: QualificationResult,
        record: dict[str, Any],
    ) -> int:
        score = 0

        if result.service_match:
            if record.get("service_match_level") == "Exact Match":
                score += 40
            else:
                score += 25

        if result.product_match:
            score += 20

        if result.location_match_level == "City Match":
            score += 20
        elif result.location_match_level == "State Match":
            score += 10
        elif result.location_match_level == "Country Match":
            score += 5

        if record.get("email"):
            score += 10

        if record.get("phone"):
            score += 10

        if record.get("website"):
            score += 5

        if record.get("linkedin"):
            score += 5

        try:
            bi_score = int(record.get("business_intelligence_score") or 0)
        except (TypeError, ValueError):
            bi_score = 0

        score += min(bi_score, 100) // 10

        return min(score, 100)

    def _label(self, score: int) -> tuple[str, str]:
        if score >= 80:
            return "Excellent Match", "★★★★★ Excellent Match"

        if score >= 60:
            return "Good Match", "★★★★ Good Match"

        if score >= 40:
            return "Possible Match", "★★★ Possible Match"

        if score >= 20:
            return "Needs Review", "★★ Needs Review"

        return "Insufficient Information", "★ Insufficient Information"
