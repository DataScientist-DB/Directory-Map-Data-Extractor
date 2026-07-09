from __future__ import annotations

import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup


class WebsiteQuality:
    """
    Extracts website quality signals for Business Intelligence scoring.
    """

    def analyze(
        self,
        html: str,
        url: str = "",
        response_time_ms: int = 0,
    ) -> dict[str, object]:
        soup = BeautifulSoup(html or "", "html.parser")

        parsed = urlparse(url or "")

        title = ""
        title_el = soup.select_one("title")
        if title_el:
            title = self._clean(title_el.get_text(" ", strip=True))

        description = ""
        desc_el = soup.select_one("meta[name='description']")
        if desc_el:
            description = self._clean(desc_el.get("content", ""))

        language = ""
        html_el = soup.select_one("html")
        if html_el:
            language = self._clean(html_el.get("lang", ""))

        generator = ""
        generator_el = soup.select_one("meta[name='generator']")
        if generator_el:
            generator = self._clean(generator_el.get("content", ""))

        favicon = ""
        icon_el = soup.select_one("link[rel*='icon'][href]")
        if icon_el:
            favicon = icon_el.get("href", "").strip()

        return {
            "website_https": parsed.scheme == "https",
            "website_title": title,
            "website_description": description,
            "website_language": language,
            "website_generator": generator,
            "favicon": favicon,
            "response_time_ms": response_time_ms,
        }

    def _clean(self, value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()
