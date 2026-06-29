from __future__ import annotations

from typing import Any

from src.enrichment.email_extractor import EmailExtractor
from src.enrichment.phone_extractor import PhoneExtractor
from src.enrichment.social_extractor import SocialExtractor
from src.enrichment.schema_extractor import SchemaExtractor
from src.enrichment.contact_link_discovery import ContactLinkDiscovery

class WebsiteEnricher:
    """
    Enriches a business record using the HTML of the company's own website.

    Version 0.3:
      - homepage
      - contact page
      - about page
      - schema.org enrichment
      - email
      - phone
      - social links
      - enrichment statistics
    """

    def __init__(self):
        self.email = EmailExtractor()
        self.phone = PhoneExtractor()
        self.social = SocialExtractor()
        self.schema = SchemaExtractor()
        self.contact_links = ContactLinkDiscovery()

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

        # Remove duplicates while preserving order
        seen = set()
        ordered = []

        for url in urls:
            if not url:
                continue
            if url not in seen:
                seen.add(url)
                ordered.append(url)

        return ordered

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
            return record

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
                self.stats.setdefault("contact_links_found", 0)
                self.stats["contact_links_found"] += len(discovered_links)

        except Exception:
            pass

        candidate_urls = self._candidate_urls(
            website,
            discovered_links,
        )

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
                self.stats["websites_visited"] += 1

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
                record["email"] = self.email.extract(html)

            if not record.get("phone"):
                record["phone"] = self.phone.extract(html)

            social = self.social.extract(html)

            if any(social.values()):
                self.stats["social_profiles_found"] += 1

            for key, value in social.items():
                if value and not record.get(key):
                    record[key] = value

            if record.get("email"):
                break

        if not original_email and record.get("email"):
            self.stats["emails_found"] += 1

        if not original_phone and record.get("phone"):
            self.stats["phones_found"] += 1

        if visited_any:
            record["website_enrichment_status"] = "success"
            record["website_enrichment_error"] = ""
        else:
            record["website_enrichment_status"] = "failed"
            record["website_enrichment_error"] = last_error

        return record