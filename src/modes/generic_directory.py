# src/modes/generic_directory.py

from typing import Any, Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.modes.generic_cards import clean_text, extract_generic_cards
from src.modes.detail_link_discovery import discover_detail_links

CANDIDATE_SELECTORS = [
    "article",
    ".card",
    ".listing",
    ".business",
    ".company",
    ".result",
    ".directory-item",
    ".search-result",
    ".member",
    ".profile",
    "li",
]
SECURITY_TERMS = [
    "performing security verification",
    "verify you are not a bot",
    "checking if the site connection is secure",
    "cf-challenge",
    "cf-turnstile",
    "challenge-platform",
    "captcha",
    "attention required",
    "just a moment",
    "please wait",
    "checking your browser",
    "ddos protection",
    "enable javascript",
    "verify you are human",
    "awswaf",
    "token.awswaf.com",
    "challenge.js",
]

def discover_card_selectors(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")
    candidates = []

    for selector in CANDIDATE_SELECTORS:
        cards = soup.select(selector)

        useful_cards = []
        for card in cards:
            text = clean_text(card.get_text(" ", strip=True))
            links = card.select("a[href]")

            if len(text) < 30:
                continue

            if len(links) == 0:
                continue

            useful_cards.append(card)

        if len(useful_cards) >= 3:
            avg_text_len = sum(
                len(clean_text(c.get_text(" ", strip=True))) for c in useful_cards
            ) / len(useful_cards)

            candidates.append({
                "selector": selector,
                "count": len(useful_cards),
                "avg_text_len": round(avg_text_len, 1),
                "score": len(useful_cards) * min(avg_text_len, 500),
            })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates


def extract_profile_links(html: str, base_url: str, max_links: int = 50) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    seen = set()

    keywords = [
        "profile",
        "company",
        "business",
        "member",
        "listing",
        "directory",
        "agency",
        "firm",
    ]

    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        label = clean_text(a.get_text(" ", strip=True))

        if not href:
            continue

        full_url = urljoin(base_url, href)
        lower = f"{href} {label}".lower()

        if any(k in lower for k in keywords):
            if full_url not in seen:
                seen.add(full_url)
                links.append(full_url)

        if len(links) >= max_links:
            break

    return links


def extract_generic_directory_page(
    html: str,
    source_url: str,
) -> Dict[str, Any]:
    """
    Generic directory discovery layer.

    It does not crawl yet.
    It analyzes one HTML page and returns:
    - discovered card selectors
    - extracted business cards
    - possible profile/detail links
    """


    html_lower = html.lower()

    if any(term in html_lower for term in SECURITY_TERMS):
        return {
            "source_url": source_url,
            "selectors": [],
            "records": [],
            "profile_links": [],
            "stats": {
                "blocked": True,
                "selector_candidates": 0,
                "records": 0,
                "profile_links": 0,
            },
        }

    selectors = discover_card_selectors(html)
    cards = extract_generic_cards(html, source_url)
    profile_links = discover_detail_links(
        html,
        source_url,
    )

    return {
        "source_url": source_url,
        "selectors": selectors,
        "records": cards,
        "profile_links": profile_links,
        "stats": {
            "selector_candidates": len(selectors),
            "records": len(cards),
            "profile_links": len(profile_links),
        },
    }
