from __future__ import annotations

from typing import Any

from src.enrichment.email_extractor import EmailExtractor
from src.enrichment.phone_extractor import PhoneExtractor
from src.enrichment.social_extractor import SocialExtractor


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
                visited_any = True

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