from __future__ import annotations

import re
from bs4 import BeautifulSoup


PHONE_RE = re.compile(
    r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}"
)


class PhoneExtractor:
    def extract(self, html: str) -> str:
        soup = BeautifulSoup(html or "", "html.parser")

        for a in soup.select("a[href^='tel:']"):
            phone = a.get("href", "").replace("tel:", "").strip()
            if phone:
                return phone

        text = soup.get_text(" ", strip=True)
        match = PHONE_RE.search(text)

        return match.group(0) if match else ""