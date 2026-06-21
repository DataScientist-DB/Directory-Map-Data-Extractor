from urllib.parse import urljoin
from bs4 import BeautifulSoup


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
        text = a.get_text(" ", strip=True).lower()

        if not href:
            continue

        combined = f"{href.lower()} {text}"

        if not any(k in combined for k in DETAIL_KEYWORDS):
            continue

        full_url = urljoin(base_url, href)

        if full_url in seen:
            continue

        seen.add(full_url)
        links.append(full_url)

        if len(links) >= limit:
            break

    return links
