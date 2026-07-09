from __future__ import annotations

from src.models.schema_record import SchemaRecord


class SchemaQuality:
    def score(self, record: SchemaRecord) -> int:
        score = 40

        fields = record.properties

        important = (
            "name",
            "telephone",
            "email",
            "address",
            "url",
        )

        for field in important:
            if fields.get(field):
                score += 10

        return min(score, 100)
