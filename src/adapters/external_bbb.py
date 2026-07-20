from __future__ import annotations

from datetime import timedelta
from typing import Any

from apify import Actor

from src.models.provider_status import ProviderStatus
from src.models.provider_result import ProviderResult
from src.models.provider_report import ProviderReport

class ExternalBBBAdapter:
    """
    Runs an external Apify BBB Actor and normalizes its output
    into UBDIP company records.

    Default provider:
        ocrad/bbb-company-scraper

    Requirements:
        - APIFY_TOKEN must be available.
        - The user's Apify account must have access to the selected Actor.
        - Paid Actors may require an active subscription.
    """

    DEFAULT_ACTOR_ID = "ocrad/bbb-company-scraper"

    KNOWN_DEMO_NAMES = {
        "ABC Plumbing Services Inc",
        "Quick Fix HVAC LLC",
        "Premier Electric Co",
        "Sunset Roofing Inc",
        "Valley Auto Repair",
    }

    def __init__(
        self,
        actor_id: str | None = None,
        timeout_seconds: int = 600,
    ) -> None:
        self.actor_id = (
            actor_id
            or self.DEFAULT_ACTOR_ID
        ).strip()

        self.timeout_seconds = max(
            int(timeout_seconds),
            60,
        )

    async def search(
        self,
        search_url: str,
        max_pages: int = 10,
        max_companies: int = 100,
        max_concurrency: int = 5,
        use_apify_proxy: bool = True,
    ) -> ProviderResult:

        """
        Run the configured external BBB Actor.

        Returns:
            (
                normalized_company_records,
                provider_report,
            )
        """

        search_url = str(
            search_url
            or ""
        ).strip()

        if not search_url:
            return ProviderResult(
                records=[],
                report=ProviderReport(
                    directory="bbb",
                    provider="external_apify_actor",
                    status=ProviderStatus.INPUT_ERROR.value,
                    reason="BBB search URL is missing.",
                    search_url="",
                ),
            )

        run_input = {
            "startUrls": [
                {
                    "url": search_url,
                }
            ],
            "maxPages": max(
                1,
                int(max_pages),
            ),
            "maxCompanies": max(
                1,
                int(max_companies),
            ),
            "maxItems": max(
                1,
                int(max_companies),
            ),
            "maxRequestsPerCrawl": max(
                int(max_companies),
                int(max_pages),
            ),
            "maxConcurrency": max(
                1,
                min(
                    int(max_concurrency),
                    20,
                ),
            ),
            "proxyConfiguration": {
                "useApifyProxy": bool(
                    use_apify_proxy
                ),
            },
        }

        Actor.log.info(
            "EXTERNAL BBB: "
            f"calling actor={self.actor_id} "
            f"url={search_url}"
        )

        try:
            actor_run = await Actor.call(
                self.actor_id,
                run_input,
                timeout=timedelta(
                    seconds=self.timeout_seconds
                ),
            )

            if actor_run is None:
                return ProviderResult(
                    records=[],
                    report=ProviderReport(
                        directory="bbb",
                        provider="external_apify_actor",
                        status=ProviderStatus.FAILED.value,
                        reason="External BBB Actor did not start.",
                        search_url=search_url,
                    ),
                )

            run_id = self._value(
                actor_run,
                "id",
                default="",
            )

            if not run_id:
                return ProviderResult(
                    records=[],
                    report=ProviderReport(
                        directory="bbb",
                        provider="external_apify_actor",
                        status=ProviderStatus.FAILED.value,
                        reason="External BBB Actor returned no run ID.",
                        search_url=search_url,
                    ),
                )

            run_status = self._value(
                actor_run,
                "status",
                default="UNKNOWN",
            )

            dataset_id = (
                self._value(
                    actor_run,
                    "defaultDatasetId",
                    default="",
                )
                or self._value(
                    actor_run,
                    "default_dataset_id",
                    default="",
                )
            )

            if not dataset_id:
                Actor.log.warning(
                    "EXTERNAL BBB: run object has no "
                    "dataset ID. "
                    f"run_type={type(actor_run).__name__} "
                    f"run_id={run_id} "
                    f"run_status={run_status}"
                )

                return ProviderResult(
                    records=[],
                    report=ProviderReport(
                        directory="bbb",
                        provider="external_apify_actor",
                        status=ProviderStatus.FAILED.value,
                        reason=(
                            "External BBB Actor completed "
                            "without a default dataset ID."
                        ),
                        search_url=search_url,
                        run_id=str(run_id),
                        run_status=str(run_status),
                    ),
                )

            apify_client = Actor.apify_client

            dataset_client = apify_client.dataset(
                str(dataset_id)
            )

            dataset_result = (
                await dataset_client.list_items(
                    limit=max(
                        1,
                        int(max_companies),
                    ),
                    clean=True,
                )
            )

            raw_items = list(
                dataset_result.items
                or []
            )

            dict_items = [
                item
                for item in raw_items
                if isinstance(
                    item,
                    dict,
                )
            ]

            if self._contains_demo_data(
                dict_items
            ):
                Actor.log.warning(
                    "EXTERNAL BBB: provider returned "
                    "demo data; records will not be "
                    "merged into UBDIP."
                )

                return ProviderResult(
                    records=[],
                    report=ProviderReport(
                        directory="bbb",
                        provider="external_apify_actor",
                        status=ProviderStatus.DEMO.value,
                        reason=(
                            "External BBB Actor returned "
                            "demonstration records."
                        ),
                        search_url=search_url,
                        run_id=str(run_id),
                        run_status=str(run_status),
                    ),
                )

            normalized: list[
                dict[str, Any]
            ] = []

            for item in dict_items:
                record = self._normalize_record(
                    item=item,
                    search_url=search_url,
                )

                if record.get(
                    "entity_name"
                ):
                    normalized.append(
                        record
                    )

            status = (
                ProviderStatus.SUCCESS.value
                if normalized
                else ProviderStatus.EMPTY.value
            )

            Actor.log.info(
                "EXTERNAL BBB: "
                f"status={status} "
                f"run_status={run_status} "
                f"records={len(normalized)}"
            )

            report = ProviderReport(
                directory="bbb",
                provider="external_apify_actor",
                status=status,
                reason="",
                records_found=len(normalized),
                search_url=search_url,
                run_id=str(run_id),
                run_status=str(run_status),
                dataset_id=str(dataset_id),
            )

            return ProviderResult(
                records=normalized,
                report=report,
            )



        except Exception as exc:

            Actor.log.exception(

                "EXTERNAL BBB: Actor execution failed."

            )

            provider_status = self._classify_exception(exc)

            Actor.log.warning(

                "EXTERNAL BBB: "

                f"classified_status={provider_status} "

                f"reason={exc}"

            )

            return ProviderResult(
                records=[],
                report=ProviderReport(
                    directory="bbb",
                    provider="external_apify_actor",
                    status=provider_status,
                    reason=repr(exc),
                    search_url=search_url,
                ),
            )

    def _classify_exception(
        self,
        exc: Exception,
    ) -> str:
        """
        Classify external Actor failures into a standard
        ProviderStatus value.
        """

        message = str(
            exc
        ).lower()

        if (
            "authentication token" in message
            or "token is not valid" in message
            or "apify token" in message
            or "payment header missing" in message
            or "payment-signature" in message
        ):
            return (
                ProviderStatus
                .AUTHENTICATION_FAILED
                .value
            )

        if (
            "must rent a paid actor" in message
            or "free trial has expired" in message
        ):
            return (
                ProviderStatus
                .RENTAL_REQUIRED
                .value
            )

        if (
            "actor was not found" in message
            or "user was not found" in message
            or "actor does not exist" in message
        ):
            return (
                ProviderStatus
                .ACTOR_UNAVAILABLE
                .value
            )

        if (
            "input is not valid" in message
            or "field input." in message
            or "input schema" in message
        ):
            return (
                ProviderStatus
                .INPUT_ERROR
                .value
            )

        if (
            "429" in message
            or "rate limit" in message
            or "too many requests" in message
        ):
            return (
                ProviderStatus
                .RATE_LIMITED
                .value
            )

        if (
            "403" in message
            or "request blocked" in message
            or "turnstile" in message
            or "cloudflare" in message
        ):
            return (
                ProviderStatus
                .BLOCKED
                .value
            )

        if (
            "exceed your remaining usage" in message
            or "remaining usage" in message
            or "upgrade to a paid plan" in message
            or "billing/subscription" in message
        ):
            return ProviderStatus.RATE_LIMITED.value

        return (
            ProviderStatus
            .RUNTIME_ERROR
            .value
        )

    def _contains_demo_data(
        self,
        items: list[dict[str, Any]],
    ) -> bool:
        """
        Detect explicit or known external-provider demo records.
        """

        if not items:
            return False

        explicit_demo = any(
            bool(
                item.get(
                    "demoMode"
                )
            )
            or str(
                item.get(
                    "mode",
                    "",
                )
            ).strip().lower()
            == "demo"
            for item in items
        )

        if explicit_demo:
            return True

        names = {
            self._text(
                item.get(
                    "businessName"
                )
                or item.get(
                    "name"
                )
                or item.get(
                    "companyName"
                )
            )
            for item in items
        }

        names.discard("")

        return (
            bool(names)
            and names.issubset(
                self.KNOWN_DEMO_NAMES
            )
        )

    def _normalize_record(
        self,
        item: dict[str, Any],
        search_url: str,
    ) -> dict[str, Any]:
        address_value = self._first(
            item,
            "address",
            "businessAddress",
            "fullAddress",
            "location",
        )

        address_parts = (
            self._address_parts(
                address_value
            )
        )

        profile_url = self._first(
            item,
            "profileUrl",
            "profile_url",
            "bbbProfileUrl",
            "bbbUrl",
            "url",
        )

        website = self._first(
            item,
            "website",
            "websiteUrl",
            "website_url",
            "businessWebsite",
        )

        phone = self._first(
            item,
            "phone",
            "phoneNumber",
            "telephone",
            "businessPhone",
        )

        categories = self._first(
            item,
            "categories",
            "category",
            "businessCategories",
            "businessCategory",
        )

        service_areas = self._first(
            item,
            "serviceAreas",
            "serviceArea",
            "areasServed",
        )

        entity_name = self._first(
            item,
            "businessName",
            "name",
            "companyName",
            "title",
        )

        email_value = self._first(
            item,
            "email",
            "emails",
            "businessEmail",
        )

        record: dict[str, Any] = {
            "entity_name": self._text(
                entity_name
            ),
            "category_names": self._join_values(
                categories
            ),
            "service_names": self._join_values(
                service_areas
            ),
            "website": self._text(
                website
            ),
            "email": self._first_text_value(
                email_value
            ),
            "phone": self._text(
                phone
            ),
            "address": address_parts[
                "address"
            ],
            "city": address_parts[
                "city"
            ],
            "state": address_parts[
                "state"
            ],
            "postal_code": address_parts[
                "postal_code"
            ],
            "country": address_parts[
                "country"
            ],
            "profile_url": self._text(
                profile_url
            ),
            "source_url": search_url,
            "source_directory": "bbb",
            "source_provider": self.actor_id,
            "architecture": "bbb",
            "crawl_mode": "external_actor",
            "bbb_rating": self._text(
                self._first(
                    item,
                    "bbbRating",
                    "rating",
                    "grade",
                )
            ),
            "bbb_accredited": self._to_bool(
                self._first(
                    item,
                    "accredited",
                    "isAccredited",
                    "bbbAccredited",
                    "accreditationStatus",
                    "bbbMember",
                )
            ),
            "bbb_business_status": self._text(
                self._first(
                    item,
                    "businessStatus",
                    "status",
                )
            ),
            "bbb_years_in_business": self._text(
                self._first(
                    item,
                    "yearsInBusiness",
                    "years_in_business",
                )
            ),
            "bbb_id": self._text(
                self._first(
                    item,
                    "bbbId",
                    "businessId",
                    "id",
                )
            ),
            "latitude": self._text(
                self._first(
                    item,
                    "latitude",
                    "lat",
                )
            ),
            "longitude": self._text(
                self._first(
                    item,
                    "longitude",
                    "lon",
                    "lng",
                )
            ),
            "raw_data": item,
        }

        social_links = self._first(
            item,
            "socialLinks",
            "social_links",
        )

        if isinstance(
            social_links,
            dict,
        ):
            record["facebook"] = (
                self._text(
                    social_links.get(
                        "facebook"
                    )
                )
            )

            record["linkedin"] = (
                self._text(
                    social_links.get(
                        "linkedin"
                    )
                )
            )

            record["instagram"] = (
                self._text(
                    social_links.get(
                        "instagram"
                    )
                )
            )

            record["youtube"] = (
                self._text(
                    social_links.get(
                        "youtube"
                    )
                )
            )

            record["twitter"] = (
                self._text(
                    social_links.get(
                        "twitter"
                    )
                    or social_links.get(
                        "x"
                    )
                )
            )

        return record

    def _address_parts(
        self,
        value: Any,
    ) -> dict[str, str]:
        result = {
            "address": "",
            "city": "",
            "state": "",
            "postal_code": "",
            "country": "",
        }

        if isinstance(
            value,
            dict,
        ):
            result["address"] = (
                self._text(
                    value.get(
                        "streetAddress"
                    )
                    or value.get(
                        "street"
                    )
                    or value.get(
                        "addressLine1"
                    )
                    or value.get(
                        "address"
                    )
                )
            )

            result["city"] = (
                self._text(
                    value.get(
                        "city"
                    )
                    or value.get(
                        "addressLocality"
                    )
                )
            )

            result["state"] = (
                self._text(
                    value.get(
                        "state"
                    )
                    or value.get(
                        "province"
                    )
                    or value.get(
                        "addressRegion"
                    )
                )
            )

            result["postal_code"] = (
                self._text(
                    value.get(
                        "postalCode"
                    )
                    or value.get(
                        "zip"
                    )
                    or value.get(
                        "zipCode"
                    )
                )
            )

            result["country"] = (
                self._text(
                    value.get(
                        "country"
                    )
                    or value.get(
                        "addressCountry"
                    )
                )
            )

            return result

        result["address"] = (
            self._text(
                value
            )
        )

        return result

    def _first(
        self,
        item: dict[str, Any],
        *keys: str,
    ) -> Any:
        for key in keys:
            value = item.get(
                key
            )

            if value not in (
                None,
                "",
                [],
                {},
            ):
                return value

        return ""

    def _first_text_value(
        self,
        value: Any,
    ) -> str:
        if isinstance(
            value,
            (
                list,
                tuple,
                set,
            ),
        ):
            for item in value:
                text = self._text(
                    item
                )

                if text:
                    return text

            return ""

        if isinstance(
            value,
            dict,
        ):
            for item in value.values():
                text = self._text(
                    item
                )

                if text:
                    return text

            return ""

        return self._text(
            value
        )

    def _join_values(
        self,
        value: Any,
    ) -> str:
        if value in (
            None,
            "",
            [],
            {},
        ):
            return ""

        if isinstance(
            value,
            dict,
        ):
            return " | ".join(
                self._text(
                    item
                )
                for item in value.values()
                if self._text(
                    item
                )
            )

        if isinstance(
            value,
            (
                list,
                tuple,
                set,
            ),
        ):
            return " | ".join(
                self._text(
                    item
                )
                for item in value
                if self._text(
                    item
                )
            )

        return self._text(
            value
        )

    def _text(
        self,
        value: Any,
    ) -> str:
        if value is None:
            return ""

        return str(
            value
        ).strip()

    def _to_bool(
        self,
        value: Any,
    ) -> bool:
        if isinstance(
            value,
            bool,
        ):
            return value

        normalized = (
            self._text(
                value
            ).lower()
        )

        return normalized in {
            "true",
            "yes",
            "y",
            "1",
            "accredited",
            "bbb accredited",
        }

    def _value(
        self,
        value: Any,
        key: str,
        default: Any = None,
    ) -> Any:
        if isinstance(
            value,
            dict,
        ):
            return value.get(
                key,
                default,
            )

        return getattr(
            value,
            key,
            default,
        )

    def _report(
        self,
        status: str,
        reason: str,
        records_found: int,
        search_url: str,
        run_id: str = "",
        run_status: str = "",
    ) -> dict[str, Any]:
        return {
            "directory": "bbb",
            "provider": "external_apify_actor",
            "provider_actor_id": self.actor_id,
            "status": status,
            "reason": reason,
            "records_found": records_found,
            "search_url": search_url,
            "run_id": run_id,
            "run_status": run_status,
        }
