def calculate_confidence(record):
    score = 0

    if record.get("email"):
        score += 40

    if record.get("phone"):
        score += 30

    if record.get("website"):
        score += 20

    if record.get("linkedin"):
        score += 10

    return min(score, 100)


def confidence_level(score: int) -> str:
    if score >= 90:
        return "High"
    elif score >= 70:
        return "Medium"
    return "Low"