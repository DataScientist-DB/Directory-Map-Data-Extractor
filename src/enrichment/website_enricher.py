from __future__ import annotations

from typing import Any

from src.enrichment.email_extractor import EmailExtractor
from src.enrichment.phone_extractor import PhoneExtractor
from src.enrichment.social_extractor import SocialExtractor


class WebsiteEnricher:
    """
    Enriches a business record using the HTML of the company's own website.

    Version 0.1:
      - email
      - phone
      - social links
    """

    def __init__(self):
        self.email = EmailExtractor()
        self.phone = PhoneExtractor()
        self.social = SocialExtractor()

    async def enrich_record_from_website(
        self,
        page,
        record: dict[str, Any],
        timeout_ms: int = 15000,
    ) -> dict[str, Any]:
        website = (record.get("website") or "").strip()

        if not website:
            return record

        try:
            await page.goto(
                website,
                wait_until="domcontentloaded",
                timeout=timeout_ms,
            )

            await page.wait_for_timeout(800)

            html = await page.content()

        except Exception as e:
            record["website_enrichment_status"] = "failed"
            record["website_enrichment_error"] = repr(e)
            return record

        if not record.get("email"):
            record["email"] = self.email.extract(html)

        if not record.get("phone"):
            record["phone"] = self.phone.extract(html)

        social = self.social.extract(html)

        for key, value in social.items():
            if value and not record.get(key):
                record[key] = value

        record["website_enrichment_status"] = "success"

        return record