from src.intelligence.company_resolver import CompanyResolver


def test_company_resolver_merges_same_domain():
    records = [
        {
            "entity_name": "Acme Engineering",
            "website": "https://www.acme.com",
            "email": "info@acme.com",
            "architecture": "bbb",
            "relevance_score": 80,
        },
        {
            "entity_name": "Acme Engineering Inc.",
            "website": "https://acme.com/contact",
            "phone": "949-555-1212",
            "architecture": "chambermaster",
            "relevance_score": 70,
        },
    ]

    resolved, duplicates_merged = CompanyResolver().resolve(records)

    assert len(resolved) == 1
    assert duplicates_merged == 1

    company = resolved[0]

    assert company["email"] == "info@acme.com"
    assert company["phone"] == "949-555-1212"
    assert company["duplicate_count"] == 2
    assert "bbb" in company["source_directories"]
    assert "chambermaster" in company["source_directories"]


def test_company_resolver_keeps_different_companies():
    records = [
        {
            "entity_name": "Acme Engineering",
            "website": "https://acme.com",
        },
        {
            "entity_name": "Beta Engineering",
            "website": "https://beta.com",
        },
    ]

    resolved, duplicates_merged = CompanyResolver().resolve(records)

    assert len(resolved) == 2
    assert duplicates_merged == 0
