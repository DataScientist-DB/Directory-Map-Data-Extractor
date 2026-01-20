from __future__ import annotations

import html
import io
import csv
from typing import Any, Dict
from pathlib import Path as _Path

from apify import Actor

from src.crawler import run_crawler
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


import json
import io
import csv
from typing import Any
from apify import Actor

def _cell(v: Any) -> str:
    """Make values safe for CSV/XLSX."""
    if v is None:
        return ""
    if isinstance(v, (str, int, float, bool)):
        return str(v)
    if isinstance(v, (list, tuple, set)):
        # join common list fields nicely
        return "; ".join(str(x) for x in v)
    if isinstance(v, dict):
        return json.dumps(v, ensure_ascii=False)
    return str(v)

async def export_dataset_to_kv(out_base: str, write_csv: bool, write_xlsx: bool) -> None:
    ds = await Actor.open_dataset()
    data = await ds.get_data(limit=999999)
    items = data.items or []

    # filter out probe rows if any exist
    items = [r for r in items if not (isinstance(r, dict) and r.get("_probe"))]

    Actor.log.info(f"EXPORT: dataset items={len(items)}")

    # Build stable columns (union of keys)
    cols = sorted({k for row in items for k in row.keys()}) if items else ["empty"]

    # ---------- CSV ----------
    if write_csv:
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(cols)
        for row in items:
            w.writerow([_cell(row.get(c)) for c in cols])

        await Actor.set_value(f"{out_base}.csv", buf.getvalue().encode("utf-8"), content_type="text/csv")
        Actor.log.info(f"Uploaded KV: {out_base}.csv")

    # ---------- XLSX ----------
    if write_xlsx:
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "data"
        ws.append(cols)

        for row in items:
            ws.append([_cell(row.get(c)) for c in cols])

        xbuf = io.BytesIO()
        wb.save(xbuf)

        await Actor.set_value(
            f"{out_base}.xlsx",
            xbuf.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        Actor.log.info(f"Uploaded KV: {out_base}.xlsx")


async def main() -> None:
    async with Actor:
        input_data = await Actor.get_input() or {}

        # Backward compatible: accept either startUrls (old) or startUrl (new schema)
        if not input_data.get("startUrls"):
            su = (input_data.get("startUrl") or "").strip()
            if su:
                input_data["startUrls"] = [{"url": su}]

        # If input is empty, apply safe demo defaults
        if not input_data:
            input_data = {
                "mode": "embedded_js",
                "startUrls": [{"url": "https://regenerationcanada.org/en/map/"}],
                "maxListings": 250,
                "maxPages": 1,
                "embedded": {
                    "enabled": True,
                    "preferJsonLd": True,
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
                "outputBaseName": "directory_listings_demo",
                "taxonomy": {"categoryMap": {}, "serviceMap": {}},
                "debug": False,
            }

        Actor.log.info(f"LOADED INPUT keys={list(input_data.keys())}")

        # PROBE: guarantees Dataset + KV store exist even if crawl fails later
        start_url = (input_data.get("startUrls") or [{}])[0].get("url")


        # KEEP only KV probe:
        await Actor.set_value(
            "PROBE.json",
            {"_probe": True, "message": "KV store works", "start_url": start_url},
            content_type="application/json",
        )


        # --- Run crawler (should push REAL rows via Actor.push_data inside crawler) ---
        crawl_info = await run_crawler(input_data) or {}
        ds = await Actor.open_dataset()
        info = await ds.get_info()
        Actor.log.info(f"DATASET itemCount={info.item_count}")

        auto_cat = crawl_info.get("category_map", {}) or {}
        auto_srv = crawl_info.get("service_map", {}) or {}

        taxonomy = input_data.get("taxonomy", {}) or {}
        manual_cat = taxonomy.get("categoryMap", {}) or {}
        manual_srv = taxonomy.get("serviceMap", {}) or {}

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
            Actor.log.info(f"DEBUG category_map sample={list(category_map.items())[:10]}")
            Actor.log.info(f"DEBUG service_map sample={list(service_map.items())[:10]}")

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
            content_type="application/json",
        )

        # Peek AFTER crawl
        ds = await Actor.open_dataset()
        peek = await ds.get_data(limit=3)
        Actor.log.info(
            f"DATASET AFTER CRAWL count={len(peek.items)} keys={(list(peek.items[0].keys()) if peek.items else [])}"
        )

        # Export from dataset -> KV (reliable on Apify Cloud)
        Actor.log.info("Starting dataset export to KV...")
        await export_dataset_to_kv(
            out_base=input_data.get("outputBaseName", "output"),
            write_csv=bool(input_data.get("outputCsv", True)),
            write_xlsx=bool(input_data.get("outputXlsx", False)),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
