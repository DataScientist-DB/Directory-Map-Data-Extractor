from __future__ import annotations

from typing import Any


class IntelligenceScore:
    """
    Computes a Business Intelligence Score for a business record.

    Version 1:
        Website.................20
        Email...................20
        Phone...................20
        LinkedIn................10
        Facebook................10
        Instagram...............5
        Twitter/X...............5
        YouTube.................5
        Schema.org..............5

        Maximum Score = 100
    """

    def score(self, record: dict[str, Any]) -> tuple[int, str]:
        score = 0

        if record.get("website"):
            score += 20

        if record.get("email"):
            score += 20

        if record.get("phone"):
            score += 20

        if record.get("linkedin"):
            score += 10

        if record.get("facebook"):
            score += 10

        if record.get("instagram"):
            score += 5

        if record.get("twitter"):
            score += 5

        if record.get("youtube"):
            score += 5

        # Schema.org-derived enrichment
        if (
            record.get("address")
            or record.get("hours")
            or record.get("postal_code")
        ):
            score += 5

        if score >= 90:
            level = "★★★★★ Excellent"
        elif score >= 70:
            level = "★★★★ Good"
        elif score >= 50:
            level = "★★★ Fair"
        elif score >= 30:
            level = "★★ Poor"
        else:
            level = "★ Very Poor"

        return score, level
