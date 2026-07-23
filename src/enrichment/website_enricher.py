from __future__ import annotations

from typing import Any

from src.enrichment.email_extractor import EmailExtractor
from src.enrichment.phone_extractor import PhoneExtractor
from src.enrichment.social_extractor import SocialExtractor
from src.enrichment.schema_extractor import SchemaExtractor
from src.enrichment.contact_link_discovery import ContactLinkDiscovery
from src.enrichment.website_quality import WebsiteQuality
from src.intelligence.intelligence_score import IntelligenceScore


class WebsiteEnricher:
    """
    Enriches a business record using the HTML of the company's own website.

    Version 0.5:
      - homepage
      - contact/about page discovery
      - schema.org enrichment
      - email extraction v2 compatible
      - phone
      - social links
      - website quality
      - cache
      - business intelligence score
      - enrichment statistics
    """

    def __init__(self):
        self.email = EmailExtractor()
        self.phone = PhoneExtractor()
        self.social = SocialExtractor()
        self.schema = SchemaExtractor()
        self.website_quality = WebsiteQuality()
        self.contact_links = ContactLinkDiscovery()
        self.intelligence = IntelligenceScore()

        self.cache: dict[str, dict[str, Any]] = {}

        self.stats = {
            "websites_visited": 0,
            "schema_hits": 0,
            "emails_found": 0,
            "phones_found": 0,
            "social_profiles_found": 0,
            "contact_links_found": 0,
        }

    def _candidate_urls(
        self,
        website: str,
        discovered: list[str] | None = None,
    ) -> list[str]:
        website = website.rstrip("/")

        urls = [
            website,
            website + "/contact",
            website + "/contact-us",
            website + "/about",
            website + "/about-us",
        ]

        if discovered:
            urls.extend(discovered)

        seen = set()
        ordered = []

        for url in urls:
            if not url:
                continue

            if url not in seen:
                seen.add(url)
                ordered.append(url)

        return ordered

    def _apply_score(self, record: dict[str, Any]) -> dict[str, Any]:
        score, grade = self.intelligence.score(record)
        record["intelligence_score"] = score
        record["intelligence_grade"] = grade
        return record

    def _apply_email_records(
        self,
        record: dict[str, Any],
        html: str,
        source: str = "html",
    ) -> None:
        """
        Supports both EmailExtractor v1 and v2.

        v1 returns:
            str

        v2 returns:
            list[EmailRecord]
        """

        extracted = self.email.extract(html)

        if not extracted:
            return

        if isinstance(extracted, str):
            if not record.get("email"):
                record["email"] = extracted
            return

        email_records = list(extracted)

        if not email_records:
            return

        email_records = sorted(
            email_records,
            key=lambda item: getattr(item, "quality_score", 0),
            reverse=True,
        )

        primary = email_records[0]

        record["email_records"] = [
            item.__dict__ if hasattr(item, "__dict__") else item
            for item in email_records
        ]

        if not record.get("email"):
            record["email"] = getattr(primary, "email", "")

        record["primary_email_quality_score"] = getattr(
            primary,
            "quality_score",
            0,
        )
        record["primary_email_classification"] = getattr(
            primary,
            "classification",
            "unknown",
        )
        record["email_count"] = len(email_records)

    def _apply_phone_records(
        self,
        record: dict[str, Any],
        html: str,
        source: str = "html",
    ) -> None:
        """
        Supports PhoneExtractor v2.
        """

        phone_records = self.phone.extract(html)

        if not phone_records:
            return

        record["phone_records"] = [
            item.__dict__ if hasattr(item, "__dict__") else item
            for item in phone_records
        ]

        primary = phone_records[0]

        if not record.get("phone"):
            record["phone"] = getattr(primary, "phone", "")


        record["primary_phone_quality_score"] = getattr(
            primary,
            "quality_score",
            0,
        )
        record["phone_count"] = len(phone_records)

    def print_statistics(self) -> None:
        print("\n===== Website Enrichment Statistics =====")

        for key, value in self.stats.items():
            print(f"{key:25}: {value}")

    async def enrich_record_from_website(
        self,
        page,
        record: dict[str, Any],
        timeout_ms: int = 15000,
    ) -> dict[str, Any]:
        website = (record.get("website") or "").strip()

        if not website:
            return self._apply_score(record)

        if website in self.cache:
            cached = self.cache[website]

            for key, value in cached.items():
                if value and not record.get(key):
                    record[key] = value

            record["website_enrichment_status"] = "cached"
            record["website_enrichment_error"] = ""

            return self._apply_score(record)

        original_email = record.get("email") or ""
        original_phone = record.get("phone") or ""

        discovered_links = []

        try:
            await page.goto(
                website,
                wait_until="domcontentloaded",
                timeout=timeout_ms,
            )

            await page.wait_for_timeout(800)

            homepage_html = await page.content()

            discovered_links = self.contact_links.discover(
                homepage_html,
                website,
            )

            if discovered_links:
                self.stats["contact_links_found"] += len(discovered_links)

        except Exception:
            pass

        candidate_urls = self._candidate_urls(
            website,
            discovered_links,
        )

        visited_any = False
        last_error = ""

        for candidate in candidate_urls:
            try:
                await page.goto(
                    candidate,
                    wait_until="domcontentloaded",
                    timeout=timeout_ms,
                )

                await page.wait_for_timeout(800)

                html = await page.content()

                visited_any = True
                self.stats["websites_visited"] += 1

                quality = self.website_quality.analyze(
                    html=html,
                    url=candidate,
                )

                for key, value in quality.items():
                    if value and not record.get(key):
                        record[key] = value

                schema = self.schema.extract(html)

                if any(v for v in schema.values() if v):
                    self.stats["schema_hits"] += 1

                if not record.get("email") and schema.get("email"):
                    record["email"] = schema["email"]

                if not record.get("phone") and schema.get("phone"):
                    record["phone"] = schema["phone"]

                if not record.get("hours") and schema.get("hours"):
                    record["hours"] = schema["hours"]

                if not record.get("address") and schema.get("street_address"):
                    record["address"] = schema["street_address"]

                if not record.get("city") and schema.get("city"):
                    record["city"] = schema["city"]

                if not record.get("state") and schema.get("state"):
                    record["state"] = schema["state"]

                if not record.get("postal_code") and schema.get("postal_code"):
                    record["postal_code"] = schema["postal_code"]

            except Exception as e:
                last_error = repr(e)
                continue

            if not record.get("email"):
                self._apply_email_records(
                    record=record,
                    html=html,
                    source=candidate,
                )

            if not record.get("phone"):
                record["phone"] = self.phone.extract(html)

            social_records = self.social.extract(html)

            if social_records:
                self.stats["social_profiles_found"] += len(social_records)

            record["social_records"] = [
                item.__dict__ if hasattr(item, "__dict__") else item
                for item in social_records
            ]

            for item in social_records:
                platform = getattr(item, "platform", "")
                url = getattr(item, "url", "")

                if platform and url and not record.get(platform):
                    record[platform] = url


            if record.get("email"):
                break

        if not original_email and record.get("email"):
            self.stats["emails_found"] += 1

        if not original_phone and record.get("phone"):
            self.stats["phones_found"] += 1

        if visited_any:
            record["website_enrichment_status"] = "success"
            record["website_enrichment_error"] = ""

            self.cache[website] = {
                "email": record.get("email", ""),
                "email_records": record.get("email_records", []),
                "email_count": record.get("email_count", 0),
                "primary_email_quality_score": record.get(
                    "primary_email_quality_score",
                    0,
                ),
                "primary_email_classification": record.get(
                    "primary_email_classification",
                    "",
                ),
                "phone": record.get("phone", ""),
                "phone_records": record.get("phone_records", []),
                "phone_count": record.get("phone_count", 0),
                "primary_phone_quality_score": record.get(
                    "primary_phone_quality_score",
                    0,
                ),
                "facebook": record.get("facebook", ""),
                "linkedin": record.get("linkedin", ""),
                "instagram": record.get("instagram", ""),
                "youtube": record.get("youtube", ""),
                "twitter": record.get("twitter", ""),
                "hours": record.get("hours", ""),
                "address": record.get("address", ""),
                "city": record.get("city", ""),
                "state": record.get("state", ""),
                "postal_code": record.get("postal_code", ""),
                "website_quality_score": record.get("website_quality_score", 0),
                "website_quality_grade": record.get("website_quality_grade", ""),
            }

        else:
            record["website_enrichment_status"] = "failed"
            record["website_enrichment_error"] = last_error

        return self._apply_score(record)
