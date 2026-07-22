from __future__ import annotations

from src.models.email_record import EmailRecord


class EmailQuality:
    def score(self, record: EmailRecord) -> int:
        score = 50

        if record.is_company_domain:
            score += 25

        if record.is_free_provider:
            score -= 35

        if record.classification == "executive":
            score += 25
        elif record.classification == "personal":
            score += 20
        elif record.classification in {"sales", "support", "finance", "hr"}:
            score += 15
        elif record.classification == "general":
            score += 10
        elif record.classification == "admin":
            score += 5

        return max(0, min(100, score))
