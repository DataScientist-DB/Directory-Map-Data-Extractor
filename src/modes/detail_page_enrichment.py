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
    "x.com": "twitter",
    "twitter.com": "twitter",
    "youtube.com": "youtube",
}


def clean_href(href: str) -> str:
    return (href or "").strip()


def enrich_detail_page(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(" ", strip=True)

    emails = set(EMAIL_RE.findall(text))
    phones = set(PHONE_RE.findall(text))

    website = ""
    socials = {
        "linkedin": "",
        "facebook": "",
        "instagram": "",
        "youtube": "",
        "twitter": "",
    }

    for a in soup.select("a[href]"):
        href = clean_href(a.get("href", ""))

        if not href:
            continue

        if href.startswith("mailto:"):
            email = href.replace("mailto:", "").split("?")[0].strip()
            if email:
                emails.add(email)
            continue

        if href.startswith("tel:"):
            phone = href.replace("tel:", "").strip()
            if phone:
                phones.add(phone)
            continue

        lower = href.lower()

        for domain, field_name in SOCIAL_DOMAINS.items():
            if domain in lower:
                socials[field_name] = href

        if href.startswith("http") and not website:
            if not any(domain in lower for domain in SOCIAL_DOMAINS):
                website = href

    email_list = sorted(emails)
    phone_list = sorted(phones)

    return {
        "email": email_list[0] if email_list else "",
        "phone": phone_list[0] if phone_list else "",
        "emails": email_list,
        "phones": phone_list,
        "website": website,
        "linkedin": socials["linkedin"],
        "facebook": socials["facebook"],
        "instagram": socials["instagram"],
        "youtube": socials["youtube"],
        "twitter": socials["twitter"],
        "socials": socials,
    }