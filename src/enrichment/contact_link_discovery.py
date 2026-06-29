from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup


class ContactLinkDiscovery:

    KEYWORDS = (
        "contact",
        "about",
        "team",
        "staff",
        "support",
        "location",
        "locations",
        "office",
    )

    def discover(
        self,
        html: str,
        base_url: str,
    ) -> list[str]:

        soup = BeautifulSoup(html or "", "html.parser")

        urls = []

        seen = set()

        for a in soup.select("a[href]"):

            href = (a.get("href") or "").strip()

            text = a.get_text(" ", strip=True).lower()

            href_low = href.lower()

            if not href:
                continue

            if href.startswith("#"):
                continue

            if href.startswith("mailto:"):
                continue

            if href.startswith("tel:"):
                continue

            candidate = f"{text} {href_low}"

            if not any(k in candidate for k in self.KEYWORDS):
                continue

            absolute = urljoin(base_url, href)

            if absolute not in seen:
                seen.add(absolute)
                urls.append(absolute)

        return urls