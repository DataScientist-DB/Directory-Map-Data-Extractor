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
    "no results found",
    "no results",
    "results not found",
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

def is_likely_business_card(name: str, text: str, website: str, email: str, phone: str) -> bool:
    name_l = (name or "").lower()
    text_l = (text or "").lower()

    reject_terms = [
        "event",
        "events",
        "tickets",
        "festival",
        "tour",
        "class",
        "classes",
        "workshop",
        "marketplace",
        "bazaar",
        "cruise",
        "parking",
        "blog",
        "story",
        "stories",
        "announcement",
        "celebration",
        "calendar",
    ]

    if any(term in name_l for term in reject_terms):
        return False

    if any(term in text_l[:300] for term in reject_terms):
        return False

    business_signals = 0

    if website:
        business_signals += 1
    if email:
        business_signals += 1
    if phone:
        business_signals += 1

    business_words = [
        "llc",
        "inc",
        "company",
        "co.",
        "services",
        "restaurant",
        "studio",
        "market",
        "shop",
        "store",
        "agency",
        "group",
        "center",
        "solutions",
        "consulting",
        "construction",
        "plumbing",
        "roofing",
        "electric",
        "realty",
        "insurance",
        "bank",
        "clinic",
        "salon",
        "cafe",
        "bakery",
    ]

    if any(word in name_l for word in business_words):
        business_signals += 1

    return business_signals >= 1

def extract_generic_cards(html: str, source_url: str = "") -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")

    candidate_selectors = [
        ".directory-item",
        ".listing",
        ".business",
        ".company",
        ".member",
        ".member-card",
        ".business-card",
        ".search-result",
        ".result",
        ".card",
        "article",
    ]

    records = []
    seen = set()
    rejected_debug = []

    for selector in candidate_selectors:
        cards = soup.select(selector)

        for sample in cards[:3]:
            txt = clean_text(sample.get_text(" ", strip=True))
            print(
                f"DEBUG SAMPLE [{selector}]:",
                txt[:150]
            )

        print(f"DEBUG selector={selector} cards={len(cards)}")

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
                    x in lower
                    for x in [
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

            email_value = dedupe(emails)
            phone_value = dedupe(phones)

            if not name and not website and not phone_value and not email_value:
                continue

            # Stronger validation:
            # A real business card should have a usable name plus at least
            # one contact/business signal.
            signal_count = 0

            if website:
                signal_count += 1
            if email_value:
                signal_count += 1
            if phone_value:
                signal_count += 1
            if social_links:
                signal_count += 1

            bad_exact_names = {
                "contact us",
                "resource directory module search",
                "south portland city hall",
                "search",
                "home",
                "menu",
                "privacy policy",
                "site map",
                "login",
                "register",
                "about us",
                "about",
                "directory search",
                "search directory",
            }

            lname = name.lower().strip()

            if lname in bad_exact_names:
                rejected_debug.append((name, phone_value, website))
                continue

            if len(name) < 3:
                rejected_debug.append((name, phone_value, website))
                continue

            if name.replace("-", "").replace(" ", "").isdigit():
                rejected_debug.append((name, phone_value, website))
                continue

            if signal_count < 1:
                rejected_debug.append((name, phone_value, website))
                continue

            if not is_business_card(
                name=name,
                website=website,
                email=email_value,
                phone=phone_value,
                text=text,
            ):
                rejected_debug.append((name, phone_value, website))
                continue

            key = (
                name.lower(),
                website.lower(),
                phone_value.lower(),
                email_value.lower(),
            )

            if key in seen:
                continue

            seen.add(key)

            if not is_likely_business_card(
                    name=name,
                    text=text,
                    website=website,
                    email=email_value,
                    phone=phone_value,
            ):
                rejected_debug.append((name, phone_value, website))
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

    for item in rejected_debug[:20]:
        print("REJECTED CARD:", item)

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