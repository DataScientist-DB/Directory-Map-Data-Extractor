from __future__ import annotations

from typing import Any

from src.enrichment.email_extractor import EmailExtractor
from src.enrichment.phone_extractor import PhoneExtractor
from src.enrichment.social_extractor import SocialExtractor
from src.enrichment.schema_extractor import SchemaExtractor

class WebsiteEnricher:
    """
    Enriches a business record using the HTML of the company's own website.

    Version 0.2:
      - homepage
      - contact page
      - about page
      - email
      - phone
      - social links
    """

    def __init__(self):
        self.email = EmailExtractor()
        self.phone = PhoneExtractor()
        self.social = SocialExtractor()
        self.schema = SchemaExtractor()

    def _candidate_urls(self, website: str) -> list[str]:
        website = website.rstrip("/")

        return [
            website,
            website + "/contact",
            website + "/contact-us",
            website + "/about",
            website + "/about-us",
        ]

    async def enrich_record_from_website(
        self,
        page,
        record: dict[str, Any],
        timeout_ms: int = 15000,
    ) -> dict[str, Any]:
        website = (record.get("website") or "").strip()

        if not website:
            return record

        candidate_urls = self._candidate_urls(website)
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
                schema = self.schema.extract(html)
                visited_any = True
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
                record["email"] = self.email.extract(html)

            if not record.get("phone"):
                record["phone"] = self.phone.extract(html)

            social = self.social.extract(html)

            for key, value in social.items():
                if value and not record.get(key):
                    record[key] = value

            if record.get("email"):
                break

        if visited_any:
            record["website_enrichment_status"] = "success"
            record["website_enrichment_error"] = ""
        else:
            record["website_enrichment_status"] = "failed"
            record["website_enrichment_error"] = last_error

        return record