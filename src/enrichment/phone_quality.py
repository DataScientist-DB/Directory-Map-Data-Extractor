from __future__ import annotations

from src.models.phone_record import PhoneRecord


class PhoneQuality:
    def score(self, record: PhoneRecord) -> int:
        score = 60

        if record.country_code:
            score += 20

        if record.classification == "office":
            score += 15

        if record.extension:
            score += 5

        return min(score, 100)
