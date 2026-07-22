from __future__ import annotations

import re

from bs4 import BeautifulSoup

from src.enrichment.phone_classifier import PhoneClassifier
from src.enrichment.phone_quality import PhoneQuality
from src.models.phone_record import PhoneRecord


PHONE_RE = re.compile(
    r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}"
)


class PhoneExtractor:
    def __init__(self):
        self.classifier = PhoneClassifier()
        self.quality = PhoneQuality()

    def _normalize(self, phone: str) -> str:
        """Normalize whitespace while preserving formatting."""
        return " ".join(phone.strip().split())

    def _build_record(self, phone: str, source: str) -> PhoneRecord:
        normalized = self._normalize(phone)

        record = PhoneRecord(
            number=normalized,
            source=source,
        )

        # Detect North American country code
        if normalized.startswith("+1") or normalized.startswith("1 "):
            record.country_code = "+1"

        record.classification = self.classifier.classify(normalized)
        record.quality_score = self.quality.score(record)
        record.confidence = 0.95 if source == "tel" else 0.85

        return record

    def extract(self, html: str) -> list[PhoneRecord]:
        soup = BeautifulSoup(html or "", "html.parser")

        phones: dict[str, PhoneRecord] = {}

        # tel: links
        for a in soup.select("a[href^='tel:']"):
            phone = (
                a.get("href", "")
                .replace("tel:", "")
                .strip()
            )

            if phone:
                normalized = self._normalize(phone)
                phones[normalized] = self._build_record(
                    normalized,
                    "tel",
                )

        # Visible text
        text = soup.get_text(" ", strip=True)

        for match in PHONE_RE.findall(text):
            normalized = self._normalize(match)

            if normalized not in phones:
                phones[normalized] = self._build_record(
                    normalized,
                    "html",
                )

        return sorted(
            phones.values(),
            key=lambda item: item.quality_score,
            reverse=True,
        )
