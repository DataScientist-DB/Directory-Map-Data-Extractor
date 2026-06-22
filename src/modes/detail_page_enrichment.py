import re
from bs4 import BeautifulSoup

EMAIL_RE = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)

PHONE_RE = re.compile(
    r"(?:\+\d{1,3}[\s.-]+)?(?:\(?\d{2,4}\)?[\s.-]+)\d{2,4}[\s.-]+\d{3,4}"
)

SOCIAL_DOMAINS = {
    "linkedin.com": "linkedin",
    "facebook.com": "facebook",
    "instagram.com": "instagram",
    "x.com": "x",
    "twitter.com": "twitter",
    "youtube.com": "youtube",
}


def enrich_detail_page(html: str):
    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(" ", strip=True)

    emails = sorted(set(EMAIL_RE.findall(text)))
    phones = sorted(set(PHONE_RE.findall(text)))

    socials = {}

    for a in soup.select("a[href]"):
        href = a.get("href", "")

        for domain, name in SOCIAL_DOMAINS.items():
            if domain in href:
                socials[name] = href

    return {
        "emails": emails,
        "phones": phones,
        "socials": socials,
    }
