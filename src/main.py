from __future__ import annotations

import json
import html
from pathlib import Path
from typing import Any, Dict

from apify import Actor

from src.crawler import run_crawler
from src.export_outputs import export_outputs
from src.taxonomy_static import RPC_CATEGORY_MAP, RSS_SERVICE_MAP

import io
import csv
from apify import Actor

async def export_dataset_to_kv(out_base: str, write_csv: bool, write_xlsx: bool) -> None:
    dataset = await Actor.open_dataset()  # default dataset
    items = (await dataset.get_data(limit=999999)).items

    if write_csv:
        buf = io.StringIO()
        if items:
            # stable columns: union of keys
            cols = sorted({k for row in items for k in row.keys()})
        else:
            cols = ["empty"]

        writer = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        for row in items:
            writer.writerow(row)

        await Actor.set_value(f"{out_base}.csv", buf.getvalue().encode("utf-8"), content_type="text/csv")

    if write_xlsx:
        # Requires openpyxl in requirements.txt
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "data"

        if items:
            cols = sorted({k for row in items for k in row.keys()})
        else:
            cols = ["empty"]

        ws.append(cols)
        for row in items:
            ws.append([row.get(c, "") for c in cols])

        xbuf = io.BytesIO()
        wb.save(xbuf)
        await Actor.set_value(
            f"{out_base}.xlsx",
            xbuf.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

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


from pathlib import Path
from apify import Actor

# keep your imports:
# from src.crawler import run_crawler
# from src.export import export_outputs
# from src.taxonomy_defaults import RPC_CATEGORY_MAP, RSS_SERVICE_MAP
# from src.helpers import _normalize_tax_map

async def main():
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
                "maxListings": 500,
                "maxPages": 1,
                "embedded": {
                    "enabled": True,
                    "preferJsonLd": True,
                    "anchorKey": "logoMedium",
                    "keys": [
                        "name", "loc", "address", "lat", "lng", "email", "tel",
                        "website", "pageURL", "categories", "products", "services",
                        "buy", "size", "results", "quote", "logo", "logoMedium"
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
                        "logoMedium": "logo_medium"
                    }
                },
                "outputCsv": True,
                "outputXlsx": True,
                "outputColumnsMode": "default",
                "outputBaseName": "output",
                "taxonomy": {"categoryMap": {}, "serviceMap": {}},
                "debug": True
            }

        Actor.log.info(f"LOADED INPUT keys={list(input_data.keys())}")

        # ✅ PROBE: guarantees Dataset + KV store are NOT empty
        start_url = (input_data.get("startUrls") or [{}])[0].get("url")
        await Actor.push_data({
            "_probe": True,
            "message": "Actor started successfully",
            "mode": input_data.get("mode"),
            "start_url": start_url
        })
        await Actor.set_value(
            "PROBE.json",
            {"_probe": True, "message": "KV store works", "start_url": start_url, "mode": input_data.get("mode")},
            content_type="application/json"
        )

        # --- Run crawler ---
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
            **_normalize_tax_map(manual_cat)
        }
        service_map = {
            **_normalize_tax_map(RSS_SERVICE_MAP),
            **_normalize_tax_map(auto_srv),
            **_normalize_tax_map(manual_srv)
        }

        if input_data.get("debug"):
            Actor.log.info(f"DEBUG category_map sample={list(category_map.items())[:10]}")
            Actor.log.info(f"DEBUG service_map sample={list(service_map.items())[:10]}")

        # Save TAXONOMY.json
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
                    "final_services": len(service_map)
                }
            },
            content_type="application/json"
        )

        # Export CSV/XLSX
        dataset_dir = Path("storage/datasets/default")
        paths = export_outputs(
            dataset_dir=dataset_dir,
            out_base=Path(input_data.get("outputBaseName", "output")),
            write_csv=bool(input_data.get("outputCsv", True)),
            write_xlsx=bool(input_data.get("outputXlsx", True)),
            columns_mode=input_data.get("outputColumnsMode", "default"),
            category_map=category_map,
            service_map=service_map
        )

        Actor.log.info(f"EXPORT FILES: {paths}")
        from pathlib import Path

        # Upload export files to Key-Value Store so they appear in Apify UI
        if isinstance(paths, dict):
            for _, rel in paths.items():
                if not rel:
                    continue
                p = Path(rel)
                if not p.is_absolute():
                    # try current dir first
                    candidates = [p, Path("storage") / rel, Path("storage/key_value_stores/default") / rel]
                else:
                    candidates = [p]

                found = None
                for c in candidates:
                    if c.exists() and c.is_file():
                        found = c
                        break

                if not found:
                    Actor.log.warning(f"Export file not found on disk: {rel} (tried {candidates})")
                    continue

                # content types for UI download
                if found.suffix.lower() == ".csv":
                    ct = "text/csv"
                elif found.suffix.lower() == ".xlsx":
                    ct = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                else:
                    ct = "application/octet-stream"

                await Actor.set_value(found.name, found.read_bytes(), content_type=ct)
                Actor.log.info(f"Uploaded to KV: {found.name} ({found.stat().st_size} bytes)")

        # ✅ If export_outputs writes files, also store them in KV for Apify UI download
        # (Optional but recommended for the challenge)
        for p in (paths or []):
            try:
                p = Path(p)
                if p.exists() and p.is_file():
                    await Actor.set_value(p.name, p.read_bytes(), content_type="application/octet-stream")
            except Exception as e:
                Actor.log.warning(f"Failed to store export file to KV: {p} ({e})")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
