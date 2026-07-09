from __future__ import annotations

from bs4 import BeautifulSoup

from src.enrichment.social_classifier import SocialClassifier
from src.enrichment.social_quality import SocialQuality
from src.models.social_record import SocialRecord


class SocialExtractor:
    def __init__(self):
        self.classifier = SocialClassifier()
        self.quality = SocialQuality()

    def _build_record(self, url: str, source: str) -> SocialRecord:
        platform = self.classifier.classify(url)

        record = SocialRecord(
            platform=platform,
            url=url.strip(),
            source=source,
        )

        record.verified = platform != "other"
        record.confidence = 0.95 if record.verified else 0.50
        record.quality_score = self.quality.score(record)

        return record

    def extract(self, html: str) -> list[SocialRecord]:
        soup = BeautifulSoup(html or "", "html.parser")

        records: dict[str, SocialRecord] = {}

        for a in soup.select("a[href]"):
            href = (a.get("href") or "").strip()

            if not href:
                continue

            platform = self.classifier.classify(href)

            if platform == "other":
                continue

            if platform not in records:
                records[platform] = self._build_record(
                    url=href,
                    source="html",
                )

        return sorted(
            records.values(),
            key=lambda item: item.quality_score,
            reverse=True,
        )
