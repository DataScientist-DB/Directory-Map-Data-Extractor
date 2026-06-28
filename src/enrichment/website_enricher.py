from __future__ import annotations

from src.enrichment.email_extractor import EmailExtractor
from src.enrichment.phone_extractor import PhoneExtractor
from src.enrichment.social_extractor import SocialExtractor


class WebsiteEnricher:
    """
    Enriches a BusinessRecord using the HTML of the company's own website.

    Version 0.1:
      - email
      - phone
      - social links
    """

    def __init__(self):
        self.email = EmailExtractor()
        self.phone = PhoneExtractor()
        self.social = SocialExtractor()

    def enrich(self, record, html: str):
        """
        Fill only missing values.
        Never overwrite values already extracted
        from the directory.
        """

        if not record.email:
            record.email = self.email.extract(html)

        if not record.phone:
            record.phone = self.phone.extract(html)

        social = self.social.extract(html)

        if not record.facebook:
            record.facebook = social["facebook"]

        if not record.linkedin:
            record.linkedin = social["linkedin"]

        if not record.instagram:
            record.instagram = social["instagram"]

        if not record.youtube:
            record.youtube = social["youtube"]

        if not record.twitter:
            record.twitter = social["twitter"]

        return record