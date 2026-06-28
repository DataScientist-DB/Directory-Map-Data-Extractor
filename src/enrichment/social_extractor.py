from __future__ import annotations

from bs4 import BeautifulSoup


class SocialExtractor:
    def extract(self, html: str) -> dict[str, str]:
        soup = BeautifulSoup(html or "", "html.parser")

        result = {
            "facebook": "",
            "linkedin": "",
            "instagram": "",
            "youtube": "",
            "twitter": "",
        }

        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()
            h = href.lower()

            if "facebook.com" in h and not result["facebook"]:
                result["facebook"] = href
            elif "linkedin.com" in h and not result["linkedin"]:
                result["linkedin"] = href
            elif "instagram.com" in h and not result["instagram"]:
                result["instagram"] = href
            elif "youtube.com" in h and not result["youtube"]:
                result["youtube"] = href
            elif ("twitter.com" in h or "x.com" in h) and not result["twitter"]:
                result["twitter"] = href

        return result