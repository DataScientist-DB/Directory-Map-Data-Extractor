from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class IndustryClassification:
    industry: str
    sector: str
    matched_term: str | None
    confidence: float
    request_type: str = "service"


@dataclass(frozen=True)
class IndustryDefinition:
    industry: str
    sector: str
    services: tuple[str, ...] = ()
    professions: tuple[str, ...] = ()
    products: tuple[str, ...] = ()
    business_types: tuple[str, ...] = ()


INDUSTRY_DEFINITIONS: tuple[IndustryDefinition, ...] = (
    # ------------------------------------------------------------------
    # TRANSPORTATION AND ENGINEERING
    # ------------------------------------------------------------------
    IndustryDefinition(
        industry="traffic engineering",
        sector="transportation and infrastructure",
        services=(
            "traffic engineering",
            "traffic impact study",
            "traffic impact assessment",
            "traffic modelling",
            "traffic simulation",
            "traffic signal design",
            "intersection analysis",
            "traffic count survey",
            "transport planning",
            "transportation planning",
            "parking study",
            "road safety audit",
            "mobility planning",
        ),
        professions=(
            "traffic engineer",
            "transport engineer",
            "transport planner",
            "transportation consultant",
            "traffic consultant",
            "transport modeller",
            "transportation modeller",
        ),
        business_types=(
            "traffic engineering company",
            "transport planning consultancy",
            "transportation engineering firm",
        ),
    ),
    IndustryDefinition(
        industry="intelligent transportation systems",
        sector="transportation and infrastructure",
        services=(
            "intelligent transportation systems",
            "its consulting",
            "traffic management systems",
            "smart mobility",
            "connected vehicle systems",
            "traffic control systems",
            "transport technology",
            "roadside systems integration",
        ),
        products=(
            "traffic signal controller",
            "variable message sign",
            "automatic traffic counter",
            "weigh in motion system",
            "anpr camera",
            "traffic sensor",
        ),
        business_types=(
            "its company",
            "transport technology company",
            "traffic systems integrator",
        ),
    ),
    IndustryDefinition(
        industry="civil engineering",
        sector="transportation and infrastructure",
        services=(
            "civil engineering",
            "infrastructure design",
            "site engineering",
            "land development engineering",
            "municipal engineering",
            "stormwater design",
            "utility design",
        ),
        professions=(
            "civil engineer",
            "infrastructure engineer",
            "municipal engineer",
        ),
        business_types=(
            "civil engineering firm",
            "engineering consultancy",
            "infrastructure consulting company",
        ),
    ),
    IndustryDefinition(
        industry="road and highway engineering",
        sector="transportation and infrastructure",
        services=(
            "road design",
            "highway design",
            "highway engineering",
            "pavement design",
            "road rehabilitation",
            "road construction supervision",
            "bridge engineering",
            "tunnel engineering",
        ),
        professions=(
            "highway engineer",
            "road engineer",
            "bridge engineer",
            "pavement engineer",
        ),
        business_types=(
            "road engineering company",
            "highway consultancy",
            "infrastructure design firm",
        ),
    ),
    IndustryDefinition(
        industry="surveying and geomatics",
        sector="transportation and infrastructure",
        services=(
            "land surveying",
            "topographic survey",
            "construction survey",
            "boundary survey",
            "geodetic survey",
            "laser scanning",
            "lidar survey",
            "drone mapping",
        ),
        professions=(
            "land surveyor",
            "geomatics engineer",
            "geospatial surveyor",
        ),
        business_types=(
            "surveying company",
            "geomatics firm",
            "land survey firm",
        ),
    ),
    IndustryDefinition(
        industry="gis and geospatial services",
        sector="technology and professional services",
        services=(
            "gis consulting",
            "geospatial analysis",
            "spatial analysis",
            "web mapping",
            "interactive gis map",
            "remote sensing",
            "location intelligence",
            "network analysis",
            "catchment analysis",
        ),
        professions=(
            "gis analyst",
            "gis consultant",
            "geospatial analyst",
            "cartographer",
        ),
        products=(
            "gis software",
            "mapping platform",
            "geospatial database",
        ),
        business_types=(
            "gis company",
            "geospatial consulting firm",
            "mapping company",
        ),
    ),

    # ------------------------------------------------------------------
    # CONSTRUCTION AND PROPERTY
    # ------------------------------------------------------------------
    IndustryDefinition(
        industry="roofing",
        sector="construction",
        services=(
            "roof installation",
            "roof repair",
            "roof replacement",
            "commercial roofing",
            "residential roofing",
            "flat roofing",
            "metal roofing",
            "roof inspection",
        ),
        professions=(
            "roofer",
            "roofing contractor",
        ),
        products=(
            "roofing materials",
            "roof shingles",
            "metal roofing panels",
        ),
        business_types=(
            "roofing company",
            "roofing contractor",
        ),
    ),
    IndustryDefinition(
        industry="general contracting",
        sector="construction",
        services=(
            "general contracting",
            "building construction",
            "commercial construction",
            "residential construction",
            "construction management",
            "design build",
            "renovation",
            "remodeling",
        ),
        professions=(
            "general contractor",
            "building contractor",
            "construction manager",
        ),
        business_types=(
            "construction company",
            "general contractor",
            "building company",
        ),
    ),
    IndustryDefinition(
        industry="heating ventilation and air conditioning",
        sector="construction",
        services=(
            "hvac installation",
            "hvac repair",
            "air conditioning repair",
            "heating repair",
            "furnace repair",
            "ventilation installation",
            "commercial hvac",
        ),
        professions=(
            "hvac contractor",
            "hvac technician",
        ),
        products=(
            "air conditioner",
            "heat pump",
            "furnace",
            "ventilation equipment",
        ),
        business_types=(
            "hvac company",
            "air conditioning contractor",
        ),
    ),
    IndustryDefinition(
        industry="plumbing",
        sector="construction",
        services=(
            "plumbing",
            "plumbing repair",
            "pipe installation",
            "drain cleaning",
            "water heater installation",
            "sewer repair",
            "commercial plumbing",
        ),
        professions=(
            "plumber",
            "plumbing contractor",
        ),
        products=(
            "plumbing supplies",
            "pipes",
            "water heaters",
        ),
        business_types=(
            "plumbing company",
            "plumbing contractor",
        ),
    ),
    IndustryDefinition(
        industry="electrical contracting",
        sector="construction",
        services=(
            "electrical installation",
            "electrical repair",
            "commercial electrical",
            "residential electrical",
            "wiring",
            "electrical inspection",
            "lighting installation",
        ),
        professions=(
            "electrician",
            "electrical contractor",
        ),
        products=(
            "electrical equipment",
            "electrical supplies",
            "lighting systems",
        ),
        business_types=(
            "electrical company",
            "electrical contractor",
        ),
    ),
    IndustryDefinition(
        industry="landscaping",
        sector="construction",
        services=(
            "landscaping",
            "landscape design",
            "lawn care",
            "garden maintenance",
            "irrigation installation",
            "tree service",
            "hardscaping",
        ),
        professions=(
            "landscaper",
            "landscape architect",
        ),
        products=(
            "landscape materials",
            "plants",
            "irrigation equipment",
        ),
        business_types=(
            "landscaping company",
            "lawn care company",
            "tree service company",
        ),
    ),
    IndustryDefinition(
        industry="real estate services",
        sector="real estate",
        services=(
            "real estate brokerage",
            "property management",
            "commercial real estate",
            "residential real estate",
            "property appraisal",
            "real estate consulting",
        ),
        professions=(
            "real estate agent",
            "realtor",
            "property manager",
            "real estate appraiser",
        ),
        business_types=(
            "real estate agency",
            "property management company",
            "real estate brokerage",
        ),
    ),

    # ------------------------------------------------------------------
    # MANUFACTURING AND INDUSTRIAL
    # ------------------------------------------------------------------
    IndustryDefinition(
        industry="manufacturing",
        sector="manufacturing and industrial",
        services=(
            "contract manufacturing",
            "custom manufacturing",
            "industrial production",
            "assembly services",
            "product manufacturing",
        ),
        professions=(
            "manufacturer",
            "production engineer",
        ),
        products=(
            "industrial products",
            "manufactured goods",
            "factory equipment",
        ),
        business_types=(
            "manufacturer",
            "manufacturing company",
            "factory",
        ),
    ),
    IndustryDefinition(
        industry="metal fabrication",
        sector="manufacturing and industrial",
        services=(
            "metal fabrication",
            "steel fabrication",
            "welding",
            "sheet metal fabrication",
            "cnc machining",
            "laser cutting",
        ),
        products=(
            "fabricated metal products",
            "steel structures",
            "machined parts",
        ),
        business_types=(
            "metal fabrication company",
            "machine shop",
            "welding company",
        ),
    ),
    IndustryDefinition(
        industry="industrial equipment",
        sector="manufacturing and industrial",
        services=(
            "industrial equipment supply",
            "equipment maintenance",
            "machinery repair",
            "equipment rental",
        ),
        products=(
            "industrial machinery",
            "construction equipment",
            "manufacturing equipment",
            "heavy equipment",
        ),
        business_types=(
            "industrial equipment supplier",
            "machinery dealer",
            "equipment rental company",
        ),
    ),
    IndustryDefinition(
        industry="food manufacturing",
        sector="manufacturing and industrial",
        services=(
            "food processing",
            "private label food manufacturing",
            "food packaging",
            "contract food manufacturing",
        ),
        products=(
            "processed food",
            "beverages",
            "bakery products",
            "frozen food",
            "packaged food",
        ),
        business_types=(
            "food manufacturer",
            "food processing company",
            "beverage manufacturer",
        ),
    ),

    # ------------------------------------------------------------------
    # TECHNOLOGY
    # ------------------------------------------------------------------
    IndustryDefinition(
        industry="software development",
        sector="technology",
        services=(
            "software development",
            "web development",
            "mobile app development",
            "saas development",
            "backend development",
            "frontend development",
            "api development",
            "cloud development",
        ),
        professions=(
            "software developer",
            "software engineer",
            "web developer",
            "app developer",
        ),
        products=(
            "software platform",
            "saas product",
            "business software",
        ),
        business_types=(
            "software company",
            "software development agency",
            "technology company",
        ),
    ),
    IndustryDefinition(
        industry="data and artificial intelligence",
        sector="technology",
        services=(
            "data science",
            "machine learning",
            "artificial intelligence consulting",
            "data analytics",
            "predictive analytics",
            "business intelligence",
            "data engineering",
        ),
        professions=(
            "data scientist",
            "machine learning engineer",
            "data engineer",
            "business intelligence analyst",
        ),
        products=(
            "ai platform",
            "analytics software",
            "machine learning solution",
        ),
        business_types=(
            "ai company",
            "data analytics company",
            "data science consultancy",
        ),
    ),
    IndustryDefinition(
        industry="web scraping and data extraction",
        sector="technology",
        services=(
            "web scraping",
            "data extraction",
            "website crawling",
            "lead scraping",
            "business directory scraping",
            "price monitoring",
            "web data collection",
        ),
        professions=(
            "web scraping developer",
            "data extraction specialist",
        ),
        products=(
            "web scraper",
            "data extraction tool",
            "scraping api",
        ),
        business_types=(
            "web scraping company",
            "data extraction company",
        ),
    ),
    IndustryDefinition(
        industry="cybersecurity",
        sector="technology",
        services=(
            "cybersecurity consulting",
            "penetration testing",
            "security audit",
            "managed security",
            "network security",
            "information security",
        ),
        professions=(
            "cybersecurity consultant",
            "security engineer",
        ),
        products=(
            "security software",
            "firewall",
            "endpoint protection",
        ),
        business_types=(
            "cybersecurity company",
            "managed security provider",
        ),
    ),

    # ------------------------------------------------------------------
    # HEALTHCARE
    # ------------------------------------------------------------------
    IndustryDefinition(
        industry="medical services",
        sector="healthcare",
        services=(
            "medical care",
            "primary care",
            "family medicine",
            "outpatient care",
            "medical consultation",
        ),
        professions=(
            "doctor",
            "physician",
            "general practitioner",
        ),
        business_types=(
            "medical clinic",
            "healthcare provider",
            "medical center",
            "hospital",
        ),
    ),
    IndustryDefinition(
        industry="dental services",
        sector="healthcare",
        services=(
            "dentistry",
            "dental care",
            "cosmetic dentistry",
            "orthodontics",
            "dental implants",
            "oral surgery",
        ),
        professions=(
            "dentist",
            "orthodontist",
            "oral surgeon",
        ),
        business_types=(
            "dental clinic",
            "dental practice",
        ),
    ),
    IndustryDefinition(
        industry="cardiology",
        sector="healthcare",
        services=(
            "cardiology",
            "heart care",
            "cardiac diagnostics",
            "cardiovascular treatment",
        ),
        professions=(
            "cardiologist",
            "cardiac surgeon",
        ),
        business_types=(
            "cardiology clinic",
            "heart center",
        ),
    ),
    IndustryDefinition(
        industry="pharmaceuticals",
        sector="healthcare",
        services=(
            "pharmaceutical manufacturing",
            "drug development",
            "clinical research",
            "pharmaceutical distribution",
        ),
        professions=(
            "pharmacist",
            "pharmaceutical researcher",
        ),
        products=(
            "pharmaceutical products",
            "medicines",
            "medical drugs",
        ),
        business_types=(
            "pharmaceutical company",
            "pharmacy",
            "drug manufacturer",
        ),
    ),

    # ------------------------------------------------------------------
    # ENERGY AND ENVIRONMENT
    # ------------------------------------------------------------------
    IndustryDefinition(
        industry="solar energy",
        sector="energy and environment",
        services=(
            "solar panel installation",
            "solar energy consulting",
            "solar system design",
            "commercial solar",
            "residential solar",
        ),
        professions=(
            "solar installer",
            "solar engineer",
        ),
        products=(
            "solar panels",
            "solar inverter",
            "solar battery",
        ),
        business_types=(
            "solar company",
            "solar installer",
            "renewable energy company",
        ),
    ),
    IndustryDefinition(
        industry="environmental consulting",
        sector="energy and environment",
        services=(
            "environmental consulting",
            "environmental impact assessment",
            "environmental monitoring",
            "sustainability consulting",
            "waste management consulting",
            "air quality assessment",
        ),
        professions=(
            "environmental consultant",
            "environmental engineer",
            "sustainability consultant",
        ),
        business_types=(
            "environmental consulting firm",
            "sustainability consultancy",
        ),
    ),
    IndustryDefinition(
        industry="water and wastewater",
        sector="energy and environment",
        services=(
            "water treatment",
            "wastewater treatment",
            "water resources engineering",
            "sewer system design",
            "drainage engineering",
            "hydraulic modelling",
        ),
        professions=(
            "water engineer",
            "wastewater engineer",
            "hydraulic engineer",
        ),
        products=(
            "water treatment equipment",
            "pumps",
            "filtration systems",
        ),
        business_types=(
            "water treatment company",
            "water engineering firm",
        ),
    ),

    # ------------------------------------------------------------------
    # PROFESSIONAL AND BUSINESS SERVICES
    # ------------------------------------------------------------------
    IndustryDefinition(
        industry="accounting",
        sector="professional services",
        services=(
            "accounting",
            "bookkeeping",
            "tax preparation",
            "audit services",
            "payroll services",
            "financial reporting",
        ),
        professions=(
            "accountant",
            "certified public accountant",
            "bookkeeper",
            "auditor",
        ),
        business_types=(
            "accounting firm",
            "cpa firm",
            "bookkeeping company",
        ),
    ),
    IndustryDefinition(
        industry="legal services",
        sector="professional services",
        services=(
            "legal services",
            "corporate law",
            "business law",
            "real estate law",
            "employment law",
            "litigation",
        ),
        professions=(
            "lawyer",
            "attorney",
            "legal consultant",
        ),
        business_types=(
            "law firm",
            "legal practice",
        ),
    ),
    IndustryDefinition(
        industry="management consulting",
        sector="professional services",
        services=(
            "management consulting",
            "business consulting",
            "strategy consulting",
            "operations consulting",
            "organizational development",
            "project management consulting",
        ),
        professions=(
            "management consultant",
            "business consultant",
            "strategy consultant",
        ),
        business_types=(
            "consulting firm",
            "management consultancy",
        ),
    ),
    IndustryDefinition(
        industry="marketing and advertising",
        sector="professional services",
        services=(
            "digital marketing",
            "advertising",
            "search engine optimization",
            "social media marketing",
            "content marketing",
            "branding",
            "lead generation",
        ),
        professions=(
            "marketing consultant",
            "seo specialist",
            "advertising specialist",
        ),
        business_types=(
            "marketing agency",
            "advertising agency",
            "seo agency",
        ),
    ),
    IndustryDefinition(
        industry="staffing and recruitment",
        sector="professional services",
        services=(
            "recruitment",
            "staffing",
            "executive search",
            "temporary staffing",
            "talent acquisition",
            "employment services",
        ),
        professions=(
            "recruiter",
            "staffing consultant",
            "headhunter",
        ),
        business_types=(
            "recruitment agency",
            "staffing agency",
            "employment agency",
        ),
    ),

    # ------------------------------------------------------------------
    # LOGISTICS, HOSPITALITY, RETAIL AND AGRICULTURE
    # ------------------------------------------------------------------
    IndustryDefinition(
        industry="logistics and freight",
        sector="transportation and logistics",
        services=(
            "freight forwarding",
            "logistics",
            "warehousing",
            "shipping",
            "last mile delivery",
            "supply chain management",
            "trucking",
        ),
        professions=(
            "freight forwarder",
            "logistics consultant",
        ),
        business_types=(
            "logistics company",
            "freight company",
            "trucking company",
            "warehouse operator",
        ),
    ),
    IndustryDefinition(
        industry="hospitality",
        sector="hospitality and tourism",
        services=(
            "hotel accommodation",
            "hospitality management",
            "event venue",
            "tourism services",
            "vacation rental",
        ),
        professions=(
            "hotel manager",
            "travel agent",
            "tour operator",
        ),
        business_types=(
            "hotel",
            "resort",
            "tour operator",
            "travel agency",
        ),
    ),
    IndustryDefinition(
        industry="restaurants and food service",
        sector="hospitality and tourism",
        services=(
            "restaurant",
            "catering",
            "food delivery",
            "event catering",
            "commercial food service",
        ),
        professions=(
            "caterer",
            "chef",
            "restaurant operator",
        ),
        business_types=(
            "restaurant",
            "catering company",
            "food service company",
        ),
    ),
    IndustryDefinition(
        industry="retail and wholesale",
        sector="retail and distribution",
        services=(
            "retail sales",
            "wholesale distribution",
            "product distribution",
            "ecommerce",
        ),
        products=(
            "consumer products",
            "wholesale goods",
            "retail products",
        ),
        business_types=(
            "retailer",
            "wholesaler",
            "distributor",
            "ecommerce company",
        ),
    ),
    IndustryDefinition(
        industry="agriculture",
        sector="agriculture and food",
        services=(
            "farming",
            "agricultural consulting",
            "crop production",
            "livestock production",
            "farm management",
            "agricultural services",
        ),
        professions=(
            "farmer",
            "agronomist",
            "agricultural consultant",
        ),
        products=(
            "agricultural products",
            "farm produce",
            "seeds",
            "fertilizer",
            "farm equipment",
        ),
        business_types=(
            "farm",
            "agricultural company",
            "farm supplier",
        ),
    ),
    IndustryDefinition(
        industry="nonprofit organizations",
        sector="nonprofit and public sector",
        services=(
            "community services",
            "charitable services",
            "social services",
            "humanitarian assistance",
            "nonprofit programs",
        ),
        business_types=(
            "nonprofit organization",
            "charity",
            "foundation",
            "community organization",
        ),
    ),
)

GENERIC_BUSINESS_WORDS: frozenset[str] = frozenset(
    {
        "agency",
        "agencies",
        "business",
        "businesses",
        "company",
        "companies",
        "consultancy",
        "consultancies",
        "consultant",
        "consultants",
        "contractor",
        "contractors",
        "dealer",
        "dealers",
        "distributor",
        "distributors",
        "firm",
        "firms",
        "organization",
        "organizations",
        "provider",
        "providers",
        "service",
        "services",
        "solution",
        "solutions",
        "specialist",
        "specialists",
        "supplier",
        "suppliers",
    }
)

# These words describe many industries and must not independently determine
# the classification. They can still contribute when they form part of an
# exact multi-word phrase such as "commercial roofing".
LOW_INFORMATION_WORDS: frozenset[str] = frozenset(
    {
        "analysis",
        "commercial",
        "consulting",
        "design",
        "development",
        "equipment",
        "installation",
        "management",
        "product",
        "products",
        "professional",
        "regional",
        "repair",
        "residential",
        "specialized",
        "system",
        "systems",
        "technology",
    }
)

REQUEST_TYPE_PRIORITY: dict[str, int] = {
    "profession": 4,
    "product": 3,
    "service": 2,
    "business_type": 1,
    "industry": 0,
}


def _normalize(value: str) -> str:
    text = value.casefold()
    text = re.sub(r"[^a-z0-9\s&+-]", " ", text)
    return " ".join(text.split())


def _singularize_word(word: str) -> str:
    """
    Apply a small set of conservative plural rules.

    This intentionally avoids a heavy NLP dependency. The rules are designed
    for common business-search forms such as companies, agencies, engineers,
    suppliers, cardiologists, and hotels.
    """
    if word.endswith("ies") and len(word) > 4:
        return f"{word[:-3]}y"

    if word.endswith("sses") and len(word) > 5:
        return word[:-2]

    if word.endswith(("ches", "shes", "xes", "zes")) and len(word) > 4:
        return word[:-2]

    if word.endswith("s") and not word.endswith(("ss", "ics", "us")):
        return word[:-1]

    return word


def _singularize_basic(value: str) -> str:
    return " ".join(_singularize_word(word) for word in value.split())


def _content_text(value: str) -> str:
    """
    Normalize a request and remove generic business modifiers.

    Examples:
        "roofing contractors" -> "roofing"
        "office furniture suppliers" -> "office furniture"
        "traffic engineering firms" -> "traffic engineering"
    """
    normalized = _normalize(value)

    content_words = [
        word
        for word in normalized.split()
        if word not in GENERIC_BUSINESS_WORDS
    ]

    return " ".join(content_words)


def _normalized_content(value: str) -> str:
    return _singularize_basic(_content_text(value))


def _definition_terms(
    definition: IndustryDefinition,
) -> tuple[tuple[str, str], ...]:
    terms: list[tuple[str, str]] = []

    terms.extend((term, "service") for term in definition.services)
    terms.extend((term, "profession") for term in definition.professions)
    terms.extend((term, "product") for term in definition.products)
    terms.extend(
        (term, "business_type")
        for term in definition.business_types
    )
    terms.append((definition.industry, "industry"))

    return tuple(terms)


@dataclass(frozen=True)
class _IndexedTerm:
    definition: IndustryDefinition
    original_term: str
    normalized_term: str
    request_type: str
    tokens: tuple[str, ...]


def _build_term_index() -> tuple[
    tuple[_IndexedTerm, ...],
    dict[str, tuple[_IndexedTerm, ...]],
    dict[str, int],
]:
    indexed_terms: list[_IndexedTerm] = []
    token_index: defaultdict[str, list[_IndexedTerm]] = defaultdict(list)
    token_industries: defaultdict[str, set[str]] = defaultdict(set)

    for definition in INDUSTRY_DEFINITIONS:
        for original_term, request_type in _definition_terms(definition):
            normalized_term = _normalized_content(original_term)

            if not normalized_term:
                continue

            tokens = tuple(dict.fromkeys(normalized_term.split()))

            indexed = _IndexedTerm(
                definition=definition,
                original_term=original_term,
                normalized_term=normalized_term,
                request_type=request_type,
                tokens=tokens,
            )
            indexed_terms.append(indexed)

            for token in tokens:
                if len(token) < 3:
                    continue

                token_index[token].append(indexed)
                token_industries[token].add(definition.industry)

    frozen_index = {
        token: tuple(records)
        for token, records in token_index.items()
    }
    industry_frequency = {
        token: len(industries)
        for token, industries in token_industries.items()
    }

    return tuple(indexed_terms), frozen_index, industry_frequency


_INDEXED_TERMS, TOKEN_INDEX, TOKEN_INDUSTRY_FREQUENCY = _build_term_index()


def _phrase_match(
    query_text: str,
) -> tuple[_IndexedTerm | None, float]:
    """
    Prefer deterministic phrase evidence.

    Exact normalized phrases are strongest. A complete multi-word taxonomy
    phrase contained in a longer request is also accepted. Single-word
    substring matches are deliberately excluded because words such as
    "commercial" and "equipment" are too broad.
    """
    query_tokens = query_text.split()
    query_token_count = len(query_tokens)

    exact_matches: list[_IndexedTerm] = []
    contained_matches: list[_IndexedTerm] = []

    padded_query = f" {query_text} "

    for indexed in _INDEXED_TERMS:
        term_text = indexed.normalized_term

        if query_text == term_text:
            exact_matches.append(indexed)
            continue

        if len(indexed.tokens) >= 2 and f" {term_text} " in padded_query:
            contained_matches.append(indexed)

    if exact_matches:
        exact_matches.sort(
            key=lambda item: (
                len(item.tokens),
                REQUEST_TYPE_PRIORITY.get(item.request_type, 0),
            ),
            reverse=True,
        )
        return exact_matches[0], 1.0

    if contained_matches:
        contained_matches.sort(
            key=lambda item: (
                len(item.tokens),
                REQUEST_TYPE_PRIORITY.get(item.request_type, 0),
            ),
            reverse=True,
        )
        best = contained_matches[0]
        coverage = len(best.tokens) / max(query_token_count, 1)
        confidence = min(0.97, 0.88 + (coverage * 0.09))
        return best, confidence

    return None, 0.0


def _token_evidence_match(
    query_text: str,
) -> tuple[_IndexedTerm | None, float]:
    """
    Use only discriminative token evidence when no phrase matches.

    A token is considered useful when it occurs in one industry only and is
    not a generic low-information word. This safely handles requests such as
    "agricultural suppliers" while leaving unknown searches such as
    "office furniture suppliers" as general business.
    """
    query_tokens = {
        token
        for token in query_text.split()
        if len(token) >= 3
        and token not in LOW_INFORMATION_WORDS
    }

    if not query_tokens:
        return None, 0.0

    industry_scores: Counter[str] = Counter()
    best_record_by_industry: dict[str, _IndexedTerm] = {}
    matched_tokens_by_industry: defaultdict[str, set[str]] = defaultdict(set)

    for token in query_tokens:
        if TOKEN_INDUSTRY_FREQUENCY.get(token, 0) != 1:
            continue

        for indexed in TOKEN_INDEX.get(token, ()):
            industry = indexed.definition.industry
            matched_tokens_by_industry[industry].add(token)

            # The same token may appear in several terms for one industry.
            # Count it only once for that industry.
            industry_scores[industry] = len(
                matched_tokens_by_industry[industry]
            )

            current = best_record_by_industry.get(industry)
            if current is None:
                best_record_by_industry[industry] = indexed
                continue

            current_overlap = len(set(current.tokens) & query_tokens)
            new_overlap = len(set(indexed.tokens) & query_tokens)

            if (
                new_overlap,
                REQUEST_TYPE_PRIORITY.get(indexed.request_type, 0),
            ) > (
                current_overlap,
                REQUEST_TYPE_PRIORITY.get(current.request_type, 0),
            ):
                best_record_by_industry[industry] = indexed

    if not industry_scores:
        return None, 0.0

    ranked = industry_scores.most_common()

    best_industry, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0

    # Do not choose an industry when evidence is tied.
    if best_score == second_score and second_score > 0:
        return None, 0.0

    best_record = best_record_by_industry[best_industry]
    matched_count = len(matched_tokens_by_industry[best_industry])
    query_count = len(query_tokens)

    if matched_count >= 2:
        confidence = min(
            0.92,
            0.76 + (0.06 * matched_count),
        )
    else:
        confidence = 0.72

    # Reduce confidence when most meaningful query tokens remain unmatched.
    coverage = matched_count / max(query_count, 1)
    confidence *= 0.75 + (0.25 * coverage)

    return best_record, round(confidence, 2)


def classify_industry(query: str) -> IndustryClassification:
    normalized_query = _normalized_content(query)

    if not normalized_query:
        return IndustryClassification(
            industry="general business",
            sector="general",
            matched_term=None,
            confidence=0.0,
            request_type="unknown",
        )

    matched_record, confidence = _phrase_match(normalized_query)

    if matched_record is None:
        matched_record, confidence = _token_evidence_match(
            normalized_query
        )

    if matched_record is None:
        return IndustryClassification(
            industry="general business",
            sector="general",
            matched_term=None,
            confidence=0.30,
            request_type="unknown",
        )

    return IndustryClassification(
        industry=matched_record.definition.industry,
        sector=matched_record.definition.sector,
        matched_term=matched_record.original_term,
        confidence=round(min(confidence, 1.0), 2),
        request_type=matched_record.request_type,
    )
