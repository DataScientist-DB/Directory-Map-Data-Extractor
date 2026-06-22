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
