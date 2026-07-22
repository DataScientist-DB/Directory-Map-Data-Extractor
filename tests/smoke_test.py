from __future__ import annotations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def check(name, func):
    try:
        func()
        print(f"✓ {name}")
        return True
    except Exception as e:
        print(f"✗ {name}")
        print(f"    {e}")
        return False


def test_business_record():
    from src.models.business_record import BusinessRecord

    BusinessRecord()


def test_enricher():
    from src.enrichment.website_enricher import WebsiteEnricher

    WebsiteEnricher()


def test_schema():
    from src.enrichment.schema_extractor import SchemaExtractor

    SchemaExtractor()


def test_contact_links():
    from src.enrichment.contact_link_discovery import ContactLinkDiscovery

    ContactLinkDiscovery()


def test_run_summary():
    from src.run_summary import print_run_summary

    assert callable(print_run_summary)


def main():

    print("\n======================================")
    print("UBDI SMOKE TEST")
    print("======================================\n")

    tests = [
        ("BusinessRecord", test_business_record),
        ("WebsiteEnricher", test_enricher),
        ("SchemaExtractor", test_schema),
        ("ContactLinkDiscovery", test_contact_links),
        ("RunSummary", test_run_summary),
    ]

    results = []

    for name, func in tests:
        results.append(check(name, func))

    print("\n======================================")

    if all(results):
        print("RESULT: PASS")
        rc = 0
    else:
        print("RESULT: FAIL")
        rc = 1

    print("======================================\n")

    return rc


if __name__ == "__main__":
    raise SystemExit(main())