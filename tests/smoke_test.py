import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.modes.profile_matching import match_profile_url

def test_profile_match():
    record = {"name": "ABC Consulting LLC"}

    links = [
        "https://example.com/profile/xyz-agency",
        "https://example.com/company/abc-consulting-llc",
    ]

    result = match_profile_url(record, links)

    assert "abc-consulting-llc" in result

if __name__ == "__main__":
    test_profile_match()
    print("PASS")
