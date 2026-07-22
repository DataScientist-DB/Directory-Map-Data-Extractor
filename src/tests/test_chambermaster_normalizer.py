from src.adapters.chambermaster import (
    ChamberMasterNormalizer,
    RawMemberProfile,
)


def test_normalize_raw_member_profile() -> None:
    profile = RawMemberProfile(
        name="Example Engineering LLC",
        phone="(555) 123-4567",
        fax="(555) 765-4321",
        email="info@example.com",
        website="https://example.com",
        facebook="https://www.facebook.com/exampleengineering",
        linkedin="https://www.linkedin.com/company/exampleengineering",
        instagram="https://www.instagram.com/exampleengineering",
        youtube="https://www.youtube.com/@exampleengineering",
        twitter="https://x.com/exampleeng",
        description=(
            "Full-service civil engineering and transportation "
            "consulting firm."
        ),
        hours="Monday-Friday, 8:00 AM-5:00 PM",
        driving_directions=(
            "Located near Central Avenue and Main Street."
        ),
        address="123 Main Street",
        city="Phoenix",
        state="AZ",
        postal_code="85001",
        category_names="Engineering",
        profile_url=(
            "https://directory.example/list/member/example"
        ),
    )

    normalizer = ChamberMasterNormalizer()

    record = normalizer.to_business_record(
        profile,
        source_url="https://directory.example",
        architecture="chambermaster",
    )

    assert record.entity_name == "Example Engineering LLC"
    assert record.phone == "(555) 123-4567"
    assert record.fax == "(555) 765-4321"
    assert record.email == "info@example.com"
    assert record.website == "https://example.com"

    assert record.facebook == (
        "https://www.facebook.com/exampleengineering"
    )
    assert record.linkedin == (
        "https://www.linkedin.com/company/exampleengineering"
    )
    assert record.instagram == (
        "https://www.instagram.com/exampleengineering"
    )
    assert record.youtube == (
        "https://www.youtube.com/@exampleengineering"
    )
    assert record.twitter == "https://x.com/exampleeng"

    assert record.description == (
        "Full-service civil engineering and transportation "
        "consulting firm."
    )
    assert record.hours == "Monday-Friday, 8:00 AM-5:00 PM"
    assert record.driving_directions == (
        "Located near Central Avenue and Main Street."
    )

    assert record.address == "123 Main Street"
    assert record.city == "Phoenix"
    assert record.state == "AZ"
    assert record.postal_code == "85001"

    assert record.profile_url == (
        "https://directory.example/list/member/example"
    )
    assert record.source_url == "https://directory.example"
    assert record.architecture == "chambermaster"
    assert record.crawl_mode == (
        "adapter_chambermaster_profile_extraction"
    )
    assert record.category_names == "Engineering"


def test_normalize_empty_raw_member_profile() -> None:
    profile = RawMemberProfile()

    normalizer = ChamberMasterNormalizer()

    record = normalizer.to_business_record(
        profile,
        source_url="",
        architecture="chambermaster",
    )

    assert record.entity_name == ""
    assert record.phone == ""
    assert record.email == ""
    assert record.website == ""
    assert record.address == ""
    assert record.description == ""
    assert record.profile_url == ""
    assert record.source_url == ""
    assert record.architecture == "chambermaster"
