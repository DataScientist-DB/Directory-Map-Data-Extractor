import pytest

from src.discovery.industry_classifier import classify_industry


@pytest.mark.parametrize(
    ("query", "expected_industry"),
    [
        ("traffic engineers", "traffic engineering"),
        ("traffic impact study consultants", "traffic engineering"),
        (
            "intelligent transportation systems companies",
            "intelligent transportation systems",
        ),
        ("civil engineering firms", "civil engineering"),
        ("GIS consulting companies", "gis and geospatial services"),
        ("roofing contractors", "roofing"),
        (
            "air conditioning repair companies",
            "heating ventilation and air conditioning",
        ),
        ("plumbers", "plumbing"),
        ("electrical contractors", "electrical contracting"),
        ("landscaping companies", "landscaping"),
        ("metal fabrication companies", "metal fabrication"),
        ("industrial machinery suppliers", "industrial equipment"),
        ("software development agencies", "software development"),
        ("web scraping services", "web scraping and data extraction"),
        ("data science consultants", "data and artificial intelligence"),
        ("cybersecurity companies", "cybersecurity"),
        ("dental clinics", "dental services"),
        ("cardiologists", "cardiology"),
        ("solar panel installers", "solar energy"),
        ("environmental consultants", "environmental consulting"),
        ("water treatment companies", "water and wastewater"),
        ("accounting firms", "accounting"),
        ("law firms", "legal services"),
        ("management consultants", "management consulting"),
        ("marketing agencies", "marketing and advertising"),
        ("staffing agencies", "staffing and recruitment"),
        ("freight forwarding companies", "logistics and freight"),
        ("hotels", "hospitality"),
        ("restaurants", "restaurants and food service"),
        ("agricultural suppliers", "agriculture"),
        ("nonprofit organizations", "nonprofit organizations"),
    ],
)
def test_classifies_business_requests(
    query: str,
    expected_industry: str,
) -> None:
    result = classify_industry(query)

    assert result.industry == expected_industry
    assert result.confidence >= 0.42


def test_detects_product_request() -> None:
    result = classify_industry("traffic signal controllers")

    assert result.industry == "intelligent transportation systems"
    assert result.request_type == "product"


def test_detects_profession_request() -> None:
    result = classify_industry("traffic engineers")

    assert result.industry == "traffic engineering"
    assert result.request_type in {"profession", "industry"}


def test_unknown_request_uses_general_business() -> None:
    result = classify_industry("specialized regional suppliers")

    assert result.industry == "general business"
    assert result.sector == "general"
@pytest.mark.parametrize(
    ("query", "expected_industry"),
    [
        ("agricultural suppliers", "agriculture"),
        ("roofing companies", "roofing"),
        ("traffic engineering consultants", "traffic engineering"),
        ("software development firms", "software development"),
    ],
)
def test_business_modifier_regressions(
    query: str,
    expected_industry: str,
):
    result = classify_industry(query)

    assert result.industry == expected_industry

    @pytest.mark.parametrize(
        "query",
        [
            "specialized regional suppliers",
            "office furniture suppliers",
            "commercial equipment providers",
            "local service companies",
        ],
    )
    def test_generic_business_words_do_not_force_industry(
        query: str,
    ):
        result = classify_industry(query)

        assert result.industry == "general business"
        assert result.sector == "general"


@pytest.mark.parametrize(
    "query",
    [
        "specialized regional suppliers",
        "office furniture suppliers",
        "commercial equipment providers",
        "local service companies",
    ],
)
def test_generic_business_words_do_not_force_industry(
    query: str,
) -> None:
    result = classify_industry(query)

    assert result.industry == "general business"
    assert result.sector == "general"
