from __future__ import annotations

import re
from bs4 import BeautifulSoup


EMAIL_RE = re.compile(
    r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
    re.IGNORECASE,
)


class EmailExtractor:
    def extract(self, html: str) -> str:
        soup = BeautifulSoup(html or "", "html.parser")

        for a in soup.select("a[href^='mailto:']"):
            email = a.get("href", "").replace("mailto:", "").split("?")[0].strip()
            if self._is_valid(email):
                return email

        text = soup.get_text(" ", strip=True)
        for match in EMAIL_RE.findall(text):
            if self._is_valid(match):
                return match

        return ""

    def _is_valid(self, email: str) -> bool:
        e = (email or "").lower().strip()

        if not e:
            return False

        blocked = [
            "example.com",
            "domain.com",
            "sentry.io",
            "wixpress.com",
            "schema.org",
        ]

        return not any(b in e for b in blocked)