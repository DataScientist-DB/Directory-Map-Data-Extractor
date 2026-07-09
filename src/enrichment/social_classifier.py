from __future__ import annotations


class SocialClassifier:

    def classify(self, url: str) -> str:

        u = url.lower()

        if "linkedin" in u:
            return "linkedin"

        if "facebook" in u:
            return "facebook"

        if "instagram" in u:
            return "instagram"

        if "youtube" in u:
            return "youtube"

        if "twitter" in u or "x.com" in u:
            return "twitter"

        return "other"
