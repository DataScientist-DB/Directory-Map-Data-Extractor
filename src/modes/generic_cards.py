# src/modes/generic_cards.py

import re
from typing import Dict, List
from bs4 import BeautifulSoup

from src.modes.card_scoring import is_business_card


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

PHONE_RE = re.compile(
    r"(?:\+\d{1,3}[\s.-]+)?(?:\(?\d{2,4}\)?[\s.-]+)\d{2,4}[\s.-]+\d{3,4}"
)

BAD_NAMES = {
    "per page",
    "next",
    "previous",
    "search",
    "submit",
    "filter",
    "sort",
    "view",
    "more",
    "home",
}

BAD_NAME_PHRASES = {
    "hockey teams",
    "countries of the world",
    "forms, searching and pagination",
    "simple example",
    "scrape this site",
    "public sandbox",
    "learn web scraping",
}


def clean_text(value: str) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def is_bad_name(name: str) -> bool:
    n = clean_text(name).lower()

    if not n:
        return True

    if n in BAD_NAMES:
        return True

    if any(phrase in n for phrase in BAD_NAME_PHRASES):
        return True

    if len(n.split()) > 12:
        return True

    return False


def extract_generic_cards(html: str, source_url: str = "") -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")

    candidate_selectors = [
        "article",
        ".card",
        ".listing",
        ".business",
        ".result",
        ".company",
        ".directory-item",
        ".search-result",
        "li",
        "div",
    ]

    records = []
    seen = set()

    for selector in candidate_selectors:
        cards = soup.select(selector)

        for card in cards:
            text = clean_text(card.get_text(" ", strip=True))

            if len(text) < 30:
                continue

            emails = EMAIL_RE.findall(text)
            phones = PHONE_RE.findall(text)

            links = []
            for a in card.select("a[href]"):
                href = a.get("href", "").strip()
                label = clean_text(a.get_text(" ", strip=True))

                if href.startswith("mailto:"):
                    emails.append(href.replace("mailto:", "").strip())

                elif href.startswith("tel:"):
                    phones.append(href.replace("tel:", "").strip())

                elif href.startswith("http"):
                    links.append({"url": href, "label": label})

            website = ""
            social_links = []

            for link in links:
                url = link["url"]
                lower = url.lower()

                if any(
                    s in lower
                    for s in [
                        "linkedin.com",
                        "facebook.com",
                        "instagram.com",
                        "twitter.com",
                        "x.com",
                        "youtube.com",
                    ]
                ):
                    social_links.append(url)
                elif not website and not any(
                        x in lower for x in [
                            "/profile",
                            "/company",
                            "/business",
                            "/member",
                            "/listing",
                            "view-profile",
                            "view_profile",
                        ]
                    ):
                    website = url

            name = guess_name(card)

            if is_bad_name(name):
                continue

            key = (name.lower(), website.lower(), text[:80].lower())
            if key in seen:
                continue
            seen.add(key)

            if not name and not website and not phones and not emails:
                continue

            email_value = dedupe(emails)
            phone_value = dedupe(phones)

            if not is_business_card(
                name=name,
                website=website,
                email=email_value,
                phone=phone_value,
                text=text,
            ):
                continue

            records.append(
                {
                    "name": name,
                    "website": website,
                    "email": email_value,
                    "phone": phone_value,
                    "social_links": dedupe(social_links),
                    "description": text[:500],
                    "source_url": source_url,
                }
            )

        if len(records) >= 3:
            break

    return records


def guess_name(card) -> str:
    for selector in ["h1", "h2", "h3", "h4", ".title", ".name", "strong", "a"]:
        el = card.select_one(selector)
        if el:
            name = clean_text(el.get_text(" ", strip=True))
            if 2 <= len(name) <= 120:
                return name

    return ""


def dedupe(values) -> str:
    cleaned = []

    for value in values:
        value = clean_text(str(value))
        if value and value not in cleaned:
            cleaned.append(value)

    return " | ".join(cleaned)