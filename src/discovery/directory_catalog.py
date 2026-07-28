from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DirectorySource:
    """
    Metadata describing a business directory or discovery source.

    This model does not contain crawler logic. The provider_id connects
    the catalog entry to an implemented provider or adapter when one
    exists.
    """

    source_id: str
    name: str
    industries: tuple[str, ...]
    countries: tuple[str, ...] = ("*",)
    regions: tuple[str, ...] = ()
    languages: tuple[str, ...] = ("en",)

    coverage: str = "national"
    specialization: str = "general"
    source_type: str = "business_directory"

    provider_id: str | None = None
    website: str | None = None

    supports_keyword_search: bool = True
    supports_location_search: bool = True
    supports_profile_pages: bool = True
    supports_phone: bool = True
    supports_email: bool = False
    supports_categories: bool = True
    supports_reviews: bool = False

    estimated_quality: float = 0.70
    estimated_speed: float = 0.70
    priority: int = 50

    enabled: bool = True
    implemented: bool = False

    @property
    def provider(self) -> str:
        """Return the executable provider identifier used by legacy callers."""
        return self.provider_id or self.source_id

    @property
    def notes(self) -> str:
        """Explain why a catalog entry cannot currently be executed."""
        if not self.enabled:
            return "Directory is disabled."
        if not self.implemented:
            return "Provider is cataloged but not yet implemented."
        return ""

    @property
    def is_general(self) -> bool:
        """Return whether this source is relevant to every industry."""
        return "*" in self.industries

    @property
    def is_specialized(self) -> bool:
        return not self.is_general

    def supports_country(self, country: str | None) -> bool:
        """Return whether the source covers the requested country."""
        if not country or "*" in self.countries:
            return True

        aliases = {
            "us": "usa",
            "u.s.": "usa",
            "u.s.a.": "usa",
            "united states": "usa",
            "united states of america": "usa",
            "uk": "united kingdom",
            "u.k.": "united kingdom",
            "gb": "united kingdom",
        }

        requested = country.strip().casefold()
        requested = aliases.get(requested, requested)

        supported = {
            aliases.get(item.strip().casefold(), item.strip().casefold())
            for item in self.countries
        }
        return requested in supported

    def supports_industry(self, industry: str | None) -> bool:
        """Return whether the source covers the classified industry."""
        if self.is_general:
            return True
        if not industry:
            return False

        requested = industry.strip().casefold()
        return any(
            item.strip().casefold() == requested
            for item in self.industries
        )


DIRECTORY_CATALOG: tuple[DirectorySource, ...] = (
    # ------------------------------------------------------------------
    # GENERAL BUSINESS SOURCES
    # ------------------------------------------------------------------
    DirectorySource(
        source_id="google_maps",
        name="Google Maps",
        industries=("*",),
        countries=("*",),
        coverage="global",
        specialization="general business",
        source_type="local_business_platform",
        provider_id="google_maps",
        website="https://www.google.com/maps",
        supports_reviews=True,
        estimated_quality=0.95,
        estimated_speed=0.85,
        priority=100,
        implemented=True,
    ),
    DirectorySource(
        source_id="bbb",
        name="Better Business Bureau",
        industries=("*",),
        countries=("USA", "Canada"),
        coverage="national",
        specialization="general business",
        provider_id="bbb",
        website="https://www.bbb.org",
        supports_reviews=True,
        estimated_quality=0.90,
        estimated_speed=0.55,
        priority=92,
        implemented=True,
    ),
    DirectorySource(
        source_id="chambermaster",
        name="ChamberMaster",
        industries=("*",),
        countries=("USA",),
        coverage="regional",
        specialization="chamber of commerce members",
        provider_id="chambermaster",
        website="https://www.chambermaster.com",
        estimated_quality=0.86,
        estimated_speed=0.80,
        priority=88,
        implemented=True,
    ),
    DirectorySource(
        source_id="yellow_pages",
        name="Yellow Pages",
        industries=("*",),
        countries=("USA",),
        coverage="national",
        specialization="general business",
        provider_id="yellow_pages",
        website="https://www.yellowpages.com",
        supports_reviews=True,
        estimated_quality=0.76,
        estimated_speed=0.75,
        priority=76,
    ),
    DirectorySource(
        source_id="yelp",
        name="Yelp",
        industries=("*",),
        countries=(
            "USA",
            "Canada",
            "United Kingdom",
            "Australia",
        ),
        coverage="international",
        specialization="local businesses",
        source_type="local_business_platform",
        provider_id="yelp",
        website="https://www.yelp.com",
        supports_reviews=True,
        estimated_quality=0.84,
        estimated_speed=0.72,
        priority=80,
    ),
    DirectorySource(
        source_id="dnb",
        name="Dun & Bradstreet Business Directory",
        industries=("*",),
        countries=("*",),
        coverage="global",
        specialization="company intelligence",
        source_type="business_intelligence_database",
        provider_id="dnb",
        website="https://www.dnb.com",
        supports_location_search=False,
        estimated_quality=0.93,
        estimated_speed=0.55,
        priority=78,
    ),

    # ------------------------------------------------------------------
    # TRANSPORTATION AND ENGINEERING
    # ------------------------------------------------------------------
    DirectorySource(
        source_id="acec",
        name="American Council of Engineering Companies",
        industries=(
            "traffic engineering",
            "civil engineering",
            "road and highway engineering",
            "surveying and geomatics",
            "environmental consulting",
            "water and wastewater",
        ),
        countries=("USA",),
        coverage="national",
        specialization="engineering companies",
        source_type="professional_association",
        provider_id="acec",
        website="https://www.acec.org",
        supports_reviews=False,
        estimated_quality=0.96,
        estimated_speed=0.65,
        priority=97,
    ),
    DirectorySource(
        source_id="ite",
        name="Institute of Transportation Engineers",
        industries=(
            "traffic engineering",
            "intelligent transportation systems",
            "road and highway engineering",
        ),
        countries=("*",),
        coverage="global",
        specialization="transportation engineering",
        source_type="professional_association",
        provider_id="ite",
        website="https://www.ite.org",
        supports_location_search=False,
        supports_reviews=False,
        estimated_quality=0.96,
        estimated_speed=0.60,
        priority=96,
    ),
    DirectorySource(
        source_id="its_america",
        name="ITS America",
        industries=(
            "intelligent transportation systems",
            "traffic engineering",
        ),
        countries=("USA",),
        coverage="national",
        specialization="transportation technology",
        source_type="professional_association",
        provider_id="its_america",
        website="https://itsa.org",
        supports_location_search=False,
        supports_reviews=False,
        estimated_quality=0.94,
        estimated_speed=0.65,
        priority=94,
    ),
    DirectorySource(
        source_id="asce",
        name="American Society of Civil Engineers",
        industries=(
            "civil engineering",
            "road and highway engineering",
            "traffic engineering",
            "water and wastewater",
            "environmental consulting",
        ),
        countries=("USA",),
        coverage="national",
        specialization="civil engineering",
        source_type="professional_association",
        provider_id="asce",
        website="https://www.asce.org",
        supports_location_search=False,
        supports_reviews=False,
        estimated_quality=0.94,
        estimated_speed=0.60,
        priority=92,
    ),
    DirectorySource(
        source_id="nsps",
        name="National Society of Professional Surveyors",
        industries=("surveying and geomatics",),
        countries=("USA",),
        coverage="national",
        specialization="surveying and geomatics",
        source_type="professional_association",
        provider_id="nsps",
        website="https://www.nsps.us.com",
        estimated_quality=0.92,
        estimated_speed=0.60,
        priority=91,
    ),
    DirectorySource(
        source_id="urisa",
        name="Urban and Regional Information Systems Association",
        industries=("gis and geospatial services",),
        countries=("*",),
        coverage="international",
        specialization="gis and geospatial services",
        source_type="professional_association",
        provider_id="urisa",
        website="https://www.urisa.org",
        supports_location_search=False,
        estimated_quality=0.90,
        estimated_speed=0.60,
        priority=90,
    ),

    # ------------------------------------------------------------------
    # CONSTRUCTION AND PROPERTY
    # ------------------------------------------------------------------
    DirectorySource(
        source_id="angi",
        name="Angi",
        industries=(
            "roofing",
            "general contracting",
            "heating ventilation and air conditioning",
            "plumbing",
            "electrical contracting",
            "landscaping",
        ),
        countries=("USA",),
        coverage="national",
        specialization="home and construction services",
        source_type="service_marketplace",
        provider_id="angi",
        website="https://www.angi.com",
        supports_reviews=True,
        estimated_quality=0.83,
        estimated_speed=0.70,
        priority=89,
    ),
    DirectorySource(
        source_id="homeadvisor",
        name="HomeAdvisor",
        industries=(
            "roofing",
            "general contracting",
            "heating ventilation and air conditioning",
            "plumbing",
            "electrical contracting",
            "landscaping",
        ),
        countries=("USA",),
        coverage="national",
        specialization="home improvement contractors",
        source_type="service_marketplace",
        provider_id="homeadvisor",
        website="https://www.homeadvisor.com",
        supports_reviews=True,
        estimated_quality=0.82,
        estimated_speed=0.68,
        priority=87,
    ),
    DirectorySource(
        source_id="houzz",
        name="Houzz",
        industries=(
            "roofing",
            "general contracting",
            "landscaping",
            "real estate services",
        ),
        countries=("*",),
        coverage="global",
        specialization="construction and home design",
        source_type="service_marketplace",
        provider_id="houzz",
        website="https://www.houzz.com",
        supports_reviews=True,
        estimated_quality=0.82,
        estimated_speed=0.72,
        priority=83,
    ),
    DirectorySource(
        source_id="nahb",
        name="National Association of Home Builders",
        industries=(
            "general contracting",
            "roofing",
            "real estate services",
        ),
        countries=("USA",),
        coverage="national",
        specialization="home building",
        source_type="professional_association",
        provider_id="nahb",
        website="https://www.nahb.org",
        estimated_quality=0.91,
        estimated_speed=0.62,
        priority=88,
    ),
    DirectorySource(
        source_id="nari",
        name="National Association of the Remodeling Industry",
        industries=("general contracting",),
        countries=("USA",),
        coverage="national",
        specialization="remodeling contractors",
        source_type="professional_association",
        provider_id="nari",
        website="https://www.nari.org",
        estimated_quality=0.91,
        estimated_speed=0.62,
        priority=89,
    ),
    DirectorySource(
        source_id="realtor",
        name="Realtor Directory",
        industries=("real estate services",),
        countries=("USA",),
        coverage="national",
        specialization="real estate professionals",
        source_type="professional_directory",
        provider_id="realtor",
        website="https://www.realtor.com",
        supports_reviews=False,
        estimated_quality=0.91,
        estimated_speed=0.72,
        priority=92,
    ),

    # ------------------------------------------------------------------
    # MANUFACTURING AND INDUSTRIAL
    # ------------------------------------------------------------------
    DirectorySource(
        source_id="thomasnet",
        name="Thomasnet",
        industries=(
            "manufacturing",
            "metal fabrication",
            "industrial equipment",
            "food manufacturing",
        ),
        countries=("USA", "Canada"),
        coverage="national",
        specialization="industrial suppliers and manufacturers",
        source_type="industrial_directory",
        provider_id="thomasnet",
        website="https://www.thomasnet.com",
        estimated_quality=0.96,
        estimated_speed=0.75,
        priority=98,
    ),
    DirectorySource(
        source_id="industrynet",
        name="IndustryNet",
        industries=(
            "manufacturing",
            "metal fabrication",
            "industrial equipment",
            "food manufacturing",
        ),
        countries=("USA",),
        coverage="national",
        specialization="manufacturers and industrial suppliers",
        source_type="industrial_directory",
        provider_id="industrynet",
        website="https://www.industrynet.com",
        estimated_quality=0.89,
        estimated_speed=0.70,
        priority=90,
    ),
    DirectorySource(
        source_id="mfg",
        name="MFG",
        industries=(
            "manufacturing",
            "metal fabrication",
            "industrial equipment",
        ),
        countries=("*",),
        coverage="global",
        specialization="contract manufacturing",
        source_type="industrial_marketplace",
        provider_id="mfg",
        website="https://www.mfg.com",
        estimated_quality=0.88,
        estimated_speed=0.67,
        priority=87,
    ),

    # ------------------------------------------------------------------
    # TECHNOLOGY
    # ------------------------------------------------------------------
    DirectorySource(
        source_id="clutch",
        name="Clutch",
        industries=(
            "software development",
            "data and artificial intelligence",
            "web scraping and data extraction",
            "cybersecurity",
            "marketing and advertising",
        ),
        countries=("*",),
        coverage="global",
        specialization="business service companies",
        source_type="agency_directory",
        provider_id="clutch",
        website="https://clutch.co",
        supports_reviews=True,
        estimated_quality=0.94,
        estimated_speed=0.74,
        priority=96,
    ),
    DirectorySource(
        source_id="goodfirms",
        name="GoodFirms",
        industries=(
            "software development",
            "data and artificial intelligence",
            "web scraping and data extraction",
            "cybersecurity",
            "marketing and advertising",
        ),
        countries=("*",),
        coverage="global",
        specialization="technology service providers",
        source_type="agency_directory",
        provider_id="goodfirms",
        website="https://www.goodfirms.co",
        supports_reviews=True,
        estimated_quality=0.88,
        estimated_speed=0.74,
        priority=89,
    ),
    DirectorySource(
        source_id="designrush",
        name="DesignRush",
        industries=(
            "software development",
            "data and artificial intelligence",
            "web scraping and data extraction",
            "cybersecurity",
            "marketing and advertising",
        ),
        countries=("*",),
        coverage="global",
        specialization="technology and marketing agencies",
        source_type="agency_directory",
        provider_id="designrush",
        website="https://www.designrush.com",
        supports_reviews=True,
        estimated_quality=0.85,
        estimated_speed=0.72,
        priority=84,
    ),

    # ------------------------------------------------------------------
    # HEALTHCARE
    # ------------------------------------------------------------------
    DirectorySource(
        source_id="healthgrades",
        name="Healthgrades",
        industries=(
            "medical services",
            "dental services",
            "cardiology",
        ),
        countries=("USA",),
        coverage="national",
        specialization="healthcare providers",
        source_type="healthcare_directory",
        provider_id="healthgrades",
        website="https://www.healthgrades.com",
        supports_reviews=True,
        estimated_quality=0.94,
        estimated_speed=0.74,
        priority=96,
    ),
    DirectorySource(
        source_id="zocdoc",
        name="Zocdoc",
        industries=(
            "medical services",
            "dental services",
            "cardiology",
        ),
        countries=("USA",),
        coverage="national",
        specialization="healthcare professionals",
        source_type="healthcare_marketplace",
        provider_id="zocdoc",
        website="https://www.zocdoc.com",
        supports_reviews=True,
        estimated_quality=0.90,
        estimated_speed=0.72,
        priority=91,
    ),
    DirectorySource(
        source_id="psychology_today",
        name="Psychology Today Directory",
        industries=("medical services",),
        countries=(
            "USA",
            "Canada",
            "United Kingdom",
            "Australia",
        ),
        coverage="international",
        specialization="mental health providers",
        source_type="healthcare_directory",
        provider_id="psychology_today",
        website="https://www.psychologytoday.com",
        supports_reviews=False,
        estimated_quality=0.88,
        estimated_speed=0.72,
        priority=82,
    ),

    # ------------------------------------------------------------------
    # ENERGY AND ENVIRONMENT
    # ------------------------------------------------------------------
    DirectorySource(
        source_id="seia",
        name="Solar Energy Industries Association",
        industries=("solar energy",),
        countries=("USA",),
        coverage="national",
        specialization="solar energy companies",
        source_type="professional_association",
        provider_id="seia",
        website="https://www.seia.org",
        estimated_quality=0.95,
        estimated_speed=0.62,
        priority=96,
    ),
    DirectorySource(
        source_id="naesco",
        name="National Association of Energy Service Companies",
        industries=(
            "solar energy",
            "environmental consulting",
        ),
        countries=("USA",),
        coverage="national",
        specialization="energy services",
        source_type="professional_association",
        provider_id="naesco",
        website="https://www.naesco.org",
        estimated_quality=0.92,
        estimated_speed=0.60,
        priority=89,
    ),
    DirectorySource(
        source_id="awwa",
        name="American Water Works Association",
        industries=("water and wastewater",),
        countries=("USA", "Canada"),
        coverage="international",
        specialization="water industry",
        source_type="professional_association",
        provider_id="awwa",
        website="https://www.awwa.org",
        estimated_quality=0.96,
        estimated_speed=0.60,
        priority=96,
    ),

    # ------------------------------------------------------------------
    # PROFESSIONAL SERVICES
    # ------------------------------------------------------------------
    DirectorySource(
        source_id="aicpa",
        name="AICPA and CIMA Directory",
        industries=("accounting",),
        countries=("USA",),
        coverage="national",
        specialization="accounting professionals",
        source_type="professional_directory",
        provider_id="aicpa",
        website="https://www.aicpa-cima.com",
        estimated_quality=0.94,
        estimated_speed=0.62,
        priority=94,
    ),
    DirectorySource(
        source_id="martindale",
        name="Martindale-Hubbell",
        industries=("legal services",),
        countries=("USA", "Canada"),
        coverage="international",
        specialization="lawyers and law firms",
        source_type="professional_directory",
        provider_id="martindale",
        website="https://www.martindale.com",
        supports_reviews=True,
        estimated_quality=0.95,
        estimated_speed=0.70,
        priority=97,
    ),
    DirectorySource(
        source_id="avvo",
        name="Avvo",
        industries=("legal services",),
        countries=("USA",),
        coverage="national",
        specialization="lawyers",
        source_type="professional_directory",
        provider_id="avvo",
        website="https://www.avvo.com",
        supports_reviews=True,
        estimated_quality=0.90,
        estimated_speed=0.72,
        priority=91,
    ),
    DirectorySource(
        source_id="shrm",
        name="SHRM",
        industries=("staffing and recruitment",),
        countries=("USA",),
        coverage="national",
        specialization="human resources",
        source_type="professional_association",
        provider_id="shrm",
        website="https://www.shrm.org",
        estimated_quality=0.90,
        estimated_speed=0.60,
        priority=84,
    ),

    # ------------------------------------------------------------------
    # LOGISTICS, HOSPITALITY, FOOD AND AGRICULTURE
    # ------------------------------------------------------------------
    DirectorySource(
        source_id="freightnet",
        name="Freightnet",
        industries=("logistics and freight",),
        countries=("*",),
        coverage="global",
        specialization="freight and logistics",
        source_type="logistics_directory",
        provider_id="freightnet",
        website="https://www.freightnet.com",
        estimated_quality=0.88,
        estimated_speed=0.72,
        priority=91,
    ),
    DirectorySource(
        source_id="tripadvisor",
        name="Tripadvisor",
        industries=(
            "hospitality",
            "restaurants and food service",
        ),
        countries=("*",),
        coverage="global",
        specialization="travel and hospitality",
        source_type="travel_platform",
        provider_id="tripadvisor",
        website="https://www.tripadvisor.com",
        supports_reviews=True,
        estimated_quality=0.93,
        estimated_speed=0.77,
        priority=95,
    ),
    DirectorySource(
        source_id="opentable",
        name="OpenTable",
        industries=("restaurants and food service",),
        countries=(
            "USA",
            "Canada",
            "United Kingdom",
            "Australia",
        ),
        coverage="international",
        specialization="restaurants",
        source_type="restaurant_platform",
        provider_id="opentable",
        website="https://www.opentable.com",
        supports_reviews=True,
        estimated_quality=0.89,
        estimated_speed=0.76,
        priority=89,
    ),
    DirectorySource(
        source_id="usda_local_food",
        name="USDA Local Food Directories",
        industries=("agriculture",),
        countries=("USA",),
        coverage="national",
        specialization="agriculture and local food",
        source_type="government_directory",
        provider_id="usda_local_food",
        website="https://www.usdalocalfoodportal.com",
        estimated_quality=0.93,
        estimated_speed=0.66,
        priority=92,
    ),
    DirectorySource(
        source_id="guidestar",
        name="Candid GuideStar",
        industries=("nonprofit organizations",),
        countries=("USA",),
        coverage="national",
        specialization="nonprofit organizations",
        source_type="nonprofit_database",
        provider_id="guidestar",
        website="https://www.guidestar.org",
        supports_location_search=False,
        estimated_quality=0.96,
        estimated_speed=0.65,
        priority=97,
    ),
)


def get_directory_by_id(
    source_id: str,
) -> DirectorySource | None:
    normalized_id = source_id.strip().casefold()

    for source in DIRECTORY_CATALOG:
        if source.source_id.casefold() == normalized_id:
            return source

    return None


def get_enabled_directories() -> tuple[DirectorySource, ...]:
    return tuple(
        source
        for source in DIRECTORY_CATALOG
        if source.enabled
    )


def get_implemented_directories() -> tuple[DirectorySource, ...]:
    return tuple(
        source
        for source in DIRECTORY_CATALOG
        if source.enabled and source.implemented
    )
