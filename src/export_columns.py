from __future__ import annotations

DEFAULT_COLUMNS = [
    "entity_name",
    "category_names",
    "website",
    "email",
    "phone",

    "linkedin",
    "facebook",
    "address",
    "city",
    "state",
    "postal_code",

    "relevance_score",
    "business_intelligence_score",
    "qualification",
    "recommendation",
    "contact_ready",

    "service_match_level",
    "matched_services",
    "location_match_level",

    "qualification_reasons",
    "missing_information",

]

ADVANCED_COLUMNS = [
    "service_names",
    "products",
    "products_rpc_codes",
    "products_rpc_names",
    "contact_completeness",
    "access_status",
    "access_reason",
    "access_http_status",
    "access_pages_visited",
    "access_profiles_found",
    "access_recommendation",
    "access_strategy",
]
ALL_COLUMNS = DEFAULT_COLUMNS + ADVANCED_COLUMNS
