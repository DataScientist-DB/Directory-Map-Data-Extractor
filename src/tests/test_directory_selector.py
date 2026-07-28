from src.discovery.directory_selector import (
    DirectorySelector,
    select_directories,
)


def test_selects_general_and_specialized_sources_for_traffic_engineers():
    selection = select_directories(
        query="traffic engineers",
        location="Phoenix, AZ",
        country="USA",
    )

    selected_ids = {
        source.source_id
        for source in selection.selected
    }

    specialized_ids = {
        source.source_id
        for source in selection.specialized_sources
    }

    assert selection.classification.industry == "traffic engineering"

    assert "google_maps" in selected_ids
    assert "bbb" in selected_ids
    assert "chambermaster" in selected_ids

    assert "acec" in specialized_ids
    assert "ite" in specialized_ids
    assert "its_america" in specialized_ids


def test_general_business_query_uses_general_directories():
    selection = select_directories(
        query="office furniture suppliers",
        location="Phoenix, AZ",
        country="USA",
    )

    selected_ids = {
        source.source_id
        for source in selection.selected
    }

    assert selection.classification.industry == "general business"

    assert "google_maps" in selected_ids
    assert "bbb" in selected_ids
    assert "chambermaster" in selected_ids

    assert selection.specialized_sources == ()


def test_country_filter_excludes_usa_only_directories():
    selection = select_directories(
        query="traffic engineers",
        location="Yerevan",
        country="Armenia",
    )

    selected_ids = {
        source.source_id
        for source in selection.selected
    }

    assert "google_maps" in selected_ids
    assert "bbb" not in selected_ids
    assert "chambermaster" not in selected_ids
    assert "acec" not in selected_ids
    assert "its_america" not in selected_ids

    # ITE is configured as a global professional source.
    assert "ite" in selected_ids


def test_manufacturing_uses_industrial_directories():
    selection = select_directories(
        query="metal fabrication companies",
        location="Chicago, IL",
        country="USA",
    )

    specialized_ids = {
        source.source_id
        for source in selection.specialized_sources
    }

    assert selection.classification.industry == "metal fabrication"
    assert "thomasnet" in specialized_ids
    assert "industrynet" in specialized_ids
    assert "mfg" in specialized_ids


def test_technology_query_uses_technology_directories():
    selection = select_directories(
        query="software development companies",
        location="Austin, TX",
        country="USA",
    )

    specialized_ids = {
        source.source_id
        for source in selection.specialized_sources
    }

    assert selection.classification.industry == "software development"
    assert "clutch" in specialized_ids
    assert "goodfirms" in specialized_ids
    assert "designrush" in specialized_ids


def test_implemented_only_returns_available_providers():
    selection = select_directories(
        query="traffic engineers",
        location="Phoenix, AZ",
        country="USA",
        implemented_only=True,
    )

    selected_ids = {
        source.source_id
        for source in selection.selected
    }

    unavailable_ids = {
        source.source_id
        for source
        in selection.unavailable_specialized_sources
    }

    assert "google_maps" in selected_ids
    assert "bbb" in selected_ids
    assert "chambermaster" in selected_ids

    assert "acec" not in selected_ids
    assert "ite" not in selected_ids
    assert "its_america" not in selected_ids

    assert "acec" in unavailable_ids
    assert "ite" in unavailable_ids
    assert "its_america" in unavailable_ids


def test_directory_selector_class_interface():
    selector = DirectorySelector(
        max_general_sources=2,
        max_specialized_sources=2,
    )

    selection = selector.select(
        query="roofing contractors",
        location="Phoenix, AZ",
        country="USA",
    )

    assert len(selection.general_sources) == 2
    assert len(selection.specialized_sources) == 2
    assert selection.classification.industry == "roofing"


def test_selection_details_returns_serializable_structure():
    selector = DirectorySelector()

    details = selector.selection_details(
        query="traffic engineers",
        location="Phoenix, AZ",
        country="USA",
    )

    assert details["industry"] == "traffic engineering"
    assert "google_maps" in details["selected_directories"]
    assert "acec" in details["specialized_directories"]
