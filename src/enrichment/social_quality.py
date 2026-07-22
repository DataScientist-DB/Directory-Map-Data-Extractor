from __future__ import annotations

from src.models.social_record import SocialRecord


class SocialQuality:

    def score(self, record: SocialRecord) -> int:

        score = 60

        if record.platform == "linkedin":
            score += 30

        elif record.platform == "facebook":
            score += 20

        elif record.platform == "youtube":
            score += 15

        elif record.platform == "instagram":
            score += 10

        return min(score, 100)
