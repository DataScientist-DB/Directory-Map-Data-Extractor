from __future__ import annotations

import json

from bs4 import BeautifulSoup


class SchemaExtractor:

    def extract(self, html: str) -> dict:
        soup = BeautifulSoup(html or "", "html.parser")

        result = {
            "email": "",
            "phone": "",
            "logo": "",
            "hours": "",
            "latitude": "",
            "longitude": "",
            "business_type": "",
            "same_as": [],
            "organization": "",
            "street_address": "",
            "city": "",
            "state": "",
            "postal_code": "",
            "country": "",
        }

        for script in soup.select(
            "script[type='application/ld+json']"
        ):
            try:
                data = json.loads(script.string or script.text)

            except Exception:
                continue

            if isinstance(data, list):
                objects = data
            else:
                objects = [data]

            for obj in objects:

                if not isinstance(obj, dict):
                    continue

                if not result["email"]:
                    result["email"] = obj.get("email", "")

                if not result["phone"]:
                    result["phone"] = obj.get("telephone", "")

                if not result["logo"]:
                    result["logo"] = obj.get("logo", "")

                if not result["hours"]:
                    result["hours"] = obj.get(
                        "openingHours",
                        ""
                    )
                if not result["organization"]:
                    result["organization"] = obj.get("name", "")

                geo = obj.get("geo") or {}

                address = obj.get("address") or {}

                if isinstance(address, dict):
                    result["street_address"] = address.get(
                        "streetAddress",
                        ""
                    )

                    result["city"] = address.get(
                        "addressLocality",
                        ""
                    )

                    result["state"] = address.get(
                        "addressRegion",
                        ""
                    )

                    result["postal_code"] = address.get(
                        "postalCode",
                        ""
                    )

                    result["country"] = address.get(
                        "addressCountry",
                        ""
                    )
                if isinstance(geo, dict):

                    result["latitude"] = geo.get(
                        "latitude",
                        ""
                    )

                    result["longitude"] = geo.get(
                        "longitude",
                        ""
                    )

                if (
                    not result["business_type"]
                    and "@type" in obj
                ):
                    result["business_type"] = obj["@type"]

                same = obj.get("sameAs")

                if isinstance(same, list):
                    result["same_as"].extend(same)

        result["same_as"] = list(
            dict.fromkeys(result["same_as"])
        )

        return result