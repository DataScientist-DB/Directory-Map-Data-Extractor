from __future__ import annotations

from src.models.search_request import SearchRequest


class RequestParser:

    @staticmethod
    def parse(actor_input: dict) -> SearchRequest:

        search = actor_input.get("search", {})

        return SearchRequest(
            keyword=search.get("keyword", ""),

            services=search.get("services", []),

            products=search.get("products", []),

            industries=search.get("industries", []),

            location=search.get("location", ""),

            country=search.get("country", ""),

            directories=search.get("directories", []),

            accredited_only=search.get(
                "accreditedOnly",
                False,
            ),

            sort=search.get("sort", "Relevance"),

            max_results=search.get(
                "maxResults",
                actor_input.get("maxListings", 100),
            ),
        )
