import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

PHONE_RE = re.compile(
    r"(?:\+\d{1,3}[\s.-]+)?(?:\(?\d{2,4}\)?[\s.-]+)\d{2,4}[\s.-]+\d{3,4}"
)

COMPANY_WORDS = {
    "llc",
    "ltd",
    "inc",
    "corp",
    "company",
    "consulting",
    "services",
    "agency",
    "firm",
    "group",
    "solutions",
    "contractor",
    "plumbing",
    "electric",
    "law",
    "attorney",
    "insurance",
    "real estate",
    "construction",
    "marketing",
    "accounting",
}

BLOCKED_TERMS = {
    "countries of the world",
    "simple example",
    "learn web scraping",
    "scrape this site",
    "documentation",
    "tutorial",
}


def score_card(name, website, email, phone, text):
    score = 0

    if email:
        score += 5

    if phone:
        score += 5

    if website:
        score += 4

    if len(text) > 50:
        score += 1

    lower = f"{name} {text}".lower()

    if any(word in lower for word in COMPANY_WORDS):
        score += 2

    return score


def is_business_card(name, website, email, phone, text):

    score = score_card(
        name=name,
        website=website,
        email=email,
        phone=phone,
        text=text,
    )

    lower = f"{name} {text}".lower()

    if any(term in lower for term in BLOCKED_TERMS):
        return False

    has_business_keyword = any(
        word in lower
        for word in COMPANY_WORDS
    )

    has_strong_signal = (
        bool(email)
        or bool(phone)
        or has_business_keyword
    )

    return score >= 5 and has_strong_signal