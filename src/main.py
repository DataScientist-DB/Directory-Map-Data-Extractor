from __future__ import annotations

import json
import html
from pathlib import Path
from typing import Any, Dict

from apify import Actor

from src.crawler import run_crawler
from src.export_outputs import export_outputs
from src.taxonomy_static import RPC_CATEGORY_MAP, RSS_SERVICE_MAP


def _clean_label(v: Any) -> str:
    if v is None:
        return ""
    s = html.unescape(str(v))
    return " ".join(s.split()).strip()

def _normalize_tax_map(m: Dict[Any, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in (m or {}).items():
        kk = str(k).strip().lower()
        vv = _clean_label(v)
        if kk and vv:
            out[kk] = vv
    return out


async def main():
    async with Actor:
        input_data = await Actor.get_input() or {}

        if not input_data and Path("INPUT.json").exists():
            input_data = json.loads(Path("INPUT.json").read_text(encoding="utf-8"))

        if not input_data:
            input_data = {
                "mode": "embedded_js",
                "startUrls": [{"url": "https://regenerationcanada.org/en/map/"}],
                "maxListings": 500,
                "maxPages": 1,
                "embedded": {
                    "anchorKey": "logoMedium",
                    "keys": [
                        "name","loc","address","lat","lng","email","tel",
                        "website","pageURL","categories","products","services",
                        "buy","size","results","quote","logo","logoMedium"
                    ],
                    "fieldMap": {
                        "name": "entity_name",
                        "loc": "location",
                        "address": "address",
                        "lat": "lat",
                        "lng": "lng",
                        "email": "email",
                        "tel": "phone",
                        "website": "website",
                        "pageURL": "profile_url",
                        "categories": "categories",
                        "products": "products",
                        "services": "services",
                        "buy": "how_to_buy",
                        "size": "size",
                        "results": "results",
                        "quote": "quote",
                        "logo": "logo",
                        "logoMedium": "logo_medium",
                    },
                },
                "outputCsv": True,
                "outputXlsx": True,
                "outputColumnsMode": "default",
                "outputBaseName": "output",
                "taxonomy": {"categoryMap": {}, "serviceMap": {}},
                "debug": True,
            }

        print("LOADED INPUT:", input_data)

        crawl_info = await run_crawler(input_data) or {}
        auto_cat = crawl_info.get("category_map", {}) or {}
        auto_srv = crawl_info.get("service_map", {}) or {}

        taxonomy = input_data.get("taxonomy", {}) or {}
        manual_cat = taxonomy.get("categoryMap", {}) or {}
        manual_srv = taxonomy.get("serviceMap", {}) or {}

        # ✅ Merge order = static defaults -> auto -> manual
        category_map = {
            **_normalize_tax_map(RPC_CATEGORY_MAP),
            **_normalize_tax_map(auto_cat),
            **_normalize_tax_map(manual_cat),
        }
        service_map = {
            **_normalize_tax_map(RSS_SERVICE_MAP),
            **_normalize_tax_map(auto_srv),
            **_normalize_tax_map(manual_srv),
        }

        if input_data.get("debug"):
            print("DEBUG category_map sample:", list(category_map.items())[:10])
            print("DEBUG service_map sample:", list(service_map.items())[:10])

        # Save TAXONOMY.json
        start_url = (input_data.get("startUrls") or [{}])[0].get("url")
        await Actor.set_value(
            "TAXONOMY.json",
            {
                "source_url": start_url,
                "category_map": category_map,
                "service_map": service_map,
                "counts": {
                    "auto_categories": len(auto_cat),
                    "auto_services": len(auto_srv),
                    "manual_categories": len(manual_cat),
                    "manual_services": len(manual_srv),
                    "final_categories": len(category_map),
                    "final_services": len(service_map),
                },
            },
        )

        dataset_dir = Path("storage/datasets/default")
        paths = export_outputs(
            dataset_dir=dataset_dir,
            out_base=Path(input_data.get("outputBaseName", "output")),
            write_csv=bool(input_data.get("outputCsv", True)),
            write_xlsx=bool(input_data.get("outputXlsx", True)),
            columns_mode=input_data.get("outputColumnsMode", "default"),
            category_map=category_map,
            service_map=service_map,
        )

        print("EXPORT FILES:", paths)
