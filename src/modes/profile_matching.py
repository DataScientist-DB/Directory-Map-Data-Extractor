import re


def normalize_name(value: str) -> str:
    value = (value or "").lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def slugify(value: str) -> str:
    value = normalize_name(value)
    return value.replace(" ", "-")


def match_profile_url(record: dict, profile_links: list[str]) -> str:
    name = record.get("name") or record.get("entity_name") or ""
    if not name or not profile_links:
        return ""

    normalized = normalize_name(name)
    slug = slugify(name)

    best_url = ""

    for url in profile_links:
        lower = url.lower()

        if slug and slug in lower:
            return url

        compact = normalized.replace(" ", "")
        if compact and compact in lower.replace("-", "").replace("_", ""):
            best_url = url

    return best_url
