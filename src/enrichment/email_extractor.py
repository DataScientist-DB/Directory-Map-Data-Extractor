from __future__ import annotations

import re

from bs4 import BeautifulSoup

from src.models.email_record import EmailRecord
from src.enrichment.email_classifier import EmailClassifier
from src.enrichment.email_quality import EmailQuality


EMAIL_RE = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
)


class EmailExtractor:
    def __init__(self):
        self.classifier = EmailClassifier()
        self.quality = EmailQuality()

    def _is_valid(self, email: str) -> bool:
        if not email:
            return False

        email = email.strip().lower()

        if "@" not in email:
            return False

        if email.startswith("@") or email.endswith("@"):
            return False

        if ".." in email:
            return False

        bad_extensions = {
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".webp",
            ".css",
            ".js",
        }

        if any(email.endswith(ext) for ext in bad_extensions):
            return False

        return bool(EMAIL_RE.fullmatch(email))

    def _build_record(self, email: str, source: str) -> EmailRecord:
        email = email.strip().lower()
        local, domain = email.split("@", 1)

        record = EmailRecord(
            email=email,
            local_part=local,
            domain=domain,
            source=source,
        )

        record.classification = self.classifier.classify(email)
        record.is_free_provider = domain in self.classifier.FREE_PROVIDERS
        record.is_company_domain = not record.is_free_provider
        record.quality_score = self.quality.score(record)
        record.confidence = 0.95 if source == "mailto" else 0.85

        return record

    def extract(self, html: str) -> list[EmailRecord]:
        soup = BeautifulSoup(html or "", "html.parser")

        emails: dict[str, EmailRecord] = {}

        for a in soup.select("a[href^='mailto:']"):
            email = (
                a.get("href", "")
                .replace("mailto:", "")
                .split("?")[0]
                .strip()
                .lower()
            )

            if self._is_valid(email) and email not in emails:
                emails[email] = self._build_record(email, "mailto")

        text = soup.get_text(" ", strip=True)

        for match in EMAIL_RE.findall(text):
            email = match.strip().lower()

            if self._is_valid(email) and email not in emails:
                emails[email] = self._build_record(email, "html")

        return sorted(
            emails.values(),
            key=lambda item: item.quality_score,
            reverse=True,
        )
