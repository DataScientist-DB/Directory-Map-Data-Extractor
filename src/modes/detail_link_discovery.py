from urllib.parse import urljoin
from bs4 import BeautifulSoup

from src.modes.generic_cards import clean_text


DETAIL_KEYWORDS = {
    "profile",
    "company",
    "business",
    "member",
    "listing",
    "agency",
    "firm",
    "consulting",
}


def discover_detail_links(html: str, base_url: str, limit: int = 100):
    soup = BeautifulSoup(html, "html.parser")

    links = []
    seen = set()

    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        label = clean_text(a.get_text(" ", strip=True))

        if not href:
            continue

        if href.startswith(("mailto:", "tel:", "#", "javascript:")):
            continue

        full_url = urljoin(base_url, href)

        base_host = urljoin(base_url, "/").split("/")[2]
        link_host = urljoin(full_url, "/").split("/")[2]

        if link_host != base_host:
            continue

        lower = f"{href} {label}".lower()

        if not any(k in lower for k in DETAIL_KEYWORDS):
            continue

        if full_url in seen:
            continue

        seen.add(full_url)
        links.append(full_url)

        if len(links) >= limit:
            break

    return links
