from __future__ import annotations

import csv
import html
import io
import json
from copy import deepcopy
from typing import Any, Dict, Iterable

from apify import Actor


from src.crawler import run_crawler
from src.discovery.request_parser import RequestParser
from src.discovery.search_orchestrator import SearchOrchestrator
from src.export_columns import ALL_COLUMNS, DEFAULT_COLUMNS
from src.intelligence.company_resolver import CompanyResolver

from src.run_summary import print_run_summary
from src.taxonomy_static import RPC_CATEGORY_MAP, RSS_SERVICE_MAP
from src.adapters.providers.default_registry import (
    build_default_provider_registry,
)
from src.discovery.provider_orchestrator import ProviderOrchestrator
def _clean_label(value: Any) -> str:
    if value is None:
        return ""
    text = html.unescape(str(value))
    return " ".join(text.split()).strip()


def _normalize_tax_map(mapping: Dict[Any, Any]) -> Dict[str, str]:
    normalized: Dict[str, str] = {}

    for key, value in (mapping or {}).items():
        normalized_key = str(key).strip().lower()
        normalized_value = _clean_label(value)

        if normalized_key and normalized_value:
            normalized[normalized_key] = normalized_value

    return normalized


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, (list, tuple, set)):
        return "; ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _codes_to_names(value: Any, mapping: Dict[Any, Any]) -> str:
    if not value:
        return ""

    normalized_map = _normalize_tax_map(mapping)

    if isinstance(value, str):
        codes = [
            item.strip().lower()
            for item in value.replace(",", ";").split(";")
        ]
    elif isinstance(value, (list, tuple, set)):
        codes = [str(item).strip().lower() for item in value]
    else:
        codes = [str(value).strip().lower()]

    names: list[str] = []
    seen: set[str] = set()

    for code in codes:
        if not code:
            continue

        name = normalized_map.get(code, code)
        if name and name not in seen:
            seen.add(name)
            names.append(name)

    return "; ".join(names)


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        value = "; ".join(str(item) for item in value if item)
    elif isinstance(value, dict):
        value = "; ".join(str(item) for item in value.values() if item)
    else:
        value = str(value)

    return " ".join(html.unescape(value).split()).strip()


def _clean_semicolon(value: Any) -> str:
    text = _clean_text(value)
    if not text:
        return ""

    parts: list[str] = []
    seen: set[str] = set()

    for part in text.split(";"):
        cleaned = " ".join(part.split()).strip(" .:-")
        if not cleaned:
            continue
        if cleaned.upper() in {"REGENERATIVE PRACTICES", "OBSERVATIONS"}:
            continue
        if cleaned not in seen:
            seen.add(cleaned)
            parts.append(cleaned)

    return "; ".join(parts)


def _split_source_text(value: Any) -> tuple[str, str]:
    text = _clean_text(value)
    if not text:
        return "", ""

    upper = text.upper()
    category_part = text
    service_part = ""

    if "REGENERATIVE PRACTICES" in upper:
        index = upper.find("REGENERATIVE PRACTICES")
        category_part = text[:index]
        service_part = text[index + len("REGENERATIVE PRACTICES") :]

    service_upper = service_part.upper()
    if "OBSERVATIONS" in service_upper:
        index = service_upper.find("OBSERVATIONS")
        service_part = service_part[:index]

    return _clean_semicolon(category_part), _clean_semicolon(service_part)


def _prepare_export_items(items: Iterable[Any]) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []

    for item in items:
        if not isinstance(item, dict) or item.get("_probe"):
            continue

        row = dict(item)
        row.setdefault("status", "success")
        row.setdefault("blocked_reason", "")

        if row.get("category_codes"):
            row["category_names_str"] = _codes_to_names(
                row.get("category_codes"),
                RPC_CATEGORY_MAP,
            )

        if row.get("service_codes"):
            row["service_names_str"] = _codes_to_names(
                row.get("service_codes"),
                RSS_SERVICE_MAP,
            )

        source_text = (
            _clean_text(row.get("products"))
            or _clean_text(row.get("results"))
            or _clean_text(row.get("quote"))
            or _clean_text(row.get("categories"))
            or _clean_text(row.get("services"))
        )

        category_text, service_text = _split_source_text(source_text)

        if not _clean_text(row.get("category_names_str")) and category_text:
            row["category_names_str"] = category_text

        if not _clean_text(row.get("service_names_str")) and service_text:
            row["service_names_str"] = service_text

        prepared.append(row)

    total = len(prepared)
    for row in prepared:
        row.setdefault("records_found", total)

    return prepared


def _normalize_requested_providers(input_data: dict[str, Any]) -> list[str]:
    requested = input_data.get("providers") or []

    if not isinstance(requested, list):
        raise ValueError("Input field 'providers' must be an array of provider names.")

    single_provider = input_data.get("provider")
    if not requested and single_provider:
        requested = [single_provider]

    normalized = [
        str(name).strip().lower()
        for name in requested
        if str(name).strip()
    ]

    return list(dict.fromkeys(normalized))


def _provider_requested(
    requested_providers: list[str],
    provider_name: str,
) -> bool:
    """No explicit list means automatic/legacy provider selection."""
    return not requested_providers or provider_name in requested_providers


def _log_provider_result(
    *,
    provider_name: str,
    status: str,
    records: int,
    error: str = "",
) -> None:
    Actor.log.info(
        "PROVIDER RESULT "
        f"name={provider_name} "
        f"status={status} "
        f"records={records} "
        f"error={error or '-'}"
    )


async def export_dataset_to_kv(
    out_base: str,
    write_csv: bool,
    write_xlsx: bool,
    columns_mode: str = "default",
) -> None:
    dataset = await Actor.open_dataset()
    data = await dataset.get_data(limit=999999)
    items = _prepare_export_items(data.items or [])

    Actor.log.info(f"EXPORT: dataset items={len(items)}")

    resolver = CompanyResolver()
    items, duplicates_merged = resolver.resolve(items)

    Actor.log.info(
        "COMPANY RESOLUTION: "
        f"records_after_merge={len(items)} "
        f"duplicates_merged={duplicates_merged}"
    )

    items.sort(
        key=lambda row: (
            int(row.get("relevance_score") or 0),
            int(row.get("business_intelligence_score") or 0),
        ),
        reverse=True,
    )

    columns = (
        ALL_COLUMNS
        if (columns_mode or "").strip().lower() == "all"
        else DEFAULT_COLUMNS
    )

    if write_csv:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(columns)

        for row in items:
            writer.writerow([_cell(row.get(column)) for column in columns])

        await Actor.set_value(
            f"{out_base}.csv",
            buffer.getvalue().encode("utf-8"),
            content_type="text/csv",
        )
        Actor.log.info(f"Uploaded KV: {out_base}.csv")

    if write_xlsx:
        from openpyxl import Workbook

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "data"
        worksheet.append(columns)

        for row in items:
            worksheet.append([_cell(row.get(column)) for column in columns])

        output = io.BytesIO()
        workbook.save(output)

        await Actor.set_value(
            f"{out_base}.xlsx",
            output.getvalue(),
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )
        Actor.log.info(f"Uploaded KV: {out_base}.xlsx")


async def main() -> None:
    async with Actor:
        input_data = await Actor.get_input() or {}

        if not input_data:
            input_data = {
                "mode": "embedded_js",
                "startUrls": [
                    {"url": "https://regenerationcanada.org/en/map/"}
                ],
                "maxListings": 250,
                "maxPages": 1,
                "embedded": {
                    "enabled": True,
                    "preferJsonLd": True,
                    "anchorKey": "logoMedium",
                    "keys": [
                        "name",
                        "loc",
                        "address",
                        "lat",
                        "lng",
                        "email",
                        "tel",
                        "website",
                        "pageURL",
                        "categories",
                        "products",
                        "services",
                        "buy",
                        "size",
                        "results",
                        "quote",
                        "logo",
                        "logoMedium",
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
                "outputBaseName": "directory_listings_demo",
                "taxonomy": {"categoryMap": {}, "serviceMap": {}},
                "debug": False,
            }

        if not input_data.get("startUrls"):
            start_url_value = str(input_data.get("startUrl") or "").strip()
            if start_url_value:
                input_data["startUrls"] = [{"url": start_url_value}]

        local_only = bool(input_data.get("localOnly", True))
        requested_providers = _normalize_requested_providers(input_data)
        enable_website_enrichment = bool(
            input_data.get("enableWebsiteEnrichment", False)
        )

        website_timeout_ms = int(
            input_data.get("websiteTimeoutMs", 15000)
        )
        Actor.log.info(f"LOADED INPUT keys={list(input_data.keys())}")
        Actor.log.info(
            "REQUESTED PROVIDERS: "
            + (", ".join(requested_providers) if requested_providers else "automatic")
        )

        start_url = (input_data.get("startUrls") or [{}])[0].get("url")

        await Actor.set_value(
            "PROBE.json",
            {
                "_probe": True,
                "message": "KV store works",
                "start_url": start_url,
            },
            content_type="application/json",
        )

        Actor.log.info("Provider Framework: ENABLED")



        search_request = RequestParser.parse(input_data)
        provider_registry = build_default_provider_registry(input_data)
        search_orchestrator = SearchOrchestrator(
            registry=provider_registry,
        )
        directory_targets = search_orchestrator.build_targets(
            input_data=input_data,
            request=search_request,
        )
        execution_details = search_orchestrator.execution_details() or {}

        for skipped in execution_details.get("skipped", []):
            Actor.log.info(
                "DIRECTORY SKIPPED: "
                f"directory={skipped.get('directory', '')} "
                f"reason={skipped.get('reason', '')} "
                f"detail={skipped.get('detail', '')}"
            )

        crawl_results: list[dict[str, Any]] = []

        if directory_targets:
            Actor.log.info(
                "MULTI-DIRECTORY TARGETS: "
                + ", ".join(
                    f"{target['directory']}={target['url']}"
                    for target in directory_targets
                )
            )

            for target in directory_targets:
                directory = target["directory"]
                url = target["url"]

                Actor.log.info(
                    "Starting directory target: "
                    f"directory={directory} url={url}"
                )

                target_input = deepcopy(input_data)
                target_input["architecture"] = directory
                target_input["startUrls"] = [{"url": url}]

                target_search = dict(target_input.get("search") or {})
                target_search["directories"] = [directory]
                target_search["autoSelectDirectories"] = False
                target_input["search"] = target_search

                bbb_provider_config = input_data.get("bbbProvider", {}) or {}

                provider_orchestrator = ProviderOrchestrator(
                    provider_registry
                )

                external_requested = _provider_requested(
                    requested_providers,
                    "bbb_external",
                )
                native_requested = _provider_requested(
                    requested_providers,
                    "bbb_native",
                )
                if directory == "bbb":
                    provider_request = {
                        "input_data": input_data,
                        "search_url": url,
                        "enable_website_enrichment": enable_website_enrichment,
                        "website_timeout_ms": website_timeout_ms,
                        "max_pages": int(
                            bbb_provider_config.get(
                                "maxPages",
                                input_data.get("maxPages", 10),
                            )
                        ),
                        "max_companies": int(
                            bbb_provider_config.get(
                                "maxCompanies",
                                input_data.get("maxListings", 100),
                            )
                        ),
                        "max_concurrency": int(
                            bbb_provider_config.get(
                                "maxConcurrency",
                                input_data.get("maxConcurrency", 1),
                            )
                        ),
                        "use_apify_proxy": bool(
                            bbb_provider_config.get("useApifyProxy", True)
                        ),
                    }


                    if local_only or not external_requested:
                        execution_results = await provider_orchestrator.search(
                            request=provider_request,
                            provider_names=["bbb_native"],
                        )
                    else:
                        execution_results = (
                            await provider_orchestrator.search_with_fallback(
                                request=provider_request,
                                primary_name="bbb_external",
                                fallback_name="bbb_native",
                                fallback_enabled=native_requested,
                            )
                        )

                    for result in execution_results:
                        Actor.log.info(
                            "[PF] "
                            f"{result.provider_name} "
                            f"status={result.status} "
                            f"records={len(result.records)}"
                        )

                        crawl_results.append(
                            {
                                "architecture": directory,
                                "directory": directory,
                                "source_url": url,
                                "target_url": url,
                                "status": result.status.value
                                if hasattr(result.status, "value")
                                else str(result.status),
                                "records_found": len(result.records),
                                "provider": result.provider_name,
                                "category_map": {},
                                "service_map": {},
                                "access_reason": result.report.reason,
                            }
                        )

                    continue

                elif directory == "chambermaster":
                    provider_request = {
                        "input_data": target_input,
                        "search_url": url,
                        "enable_website_enrichment": enable_website_enrichment,
                        "website_timeout_ms": website_timeout_ms,
                    }

                    execution_results = await provider_orchestrator.search(
                        request=provider_request,
                        provider_names=["chambermaster"],
                    )

                    crawl_results.extend(
                        result.report.metadata.get("crawler_result", {})
                        for result in execution_results
                        if result.report
                    )

                    continue

                try:
                    target_result = await run_crawler(
                        target_input,
                        enable_website_enrichment=enable_website_enrichment,
                        website_timeout_ms=website_timeout_ms,
                    ) or {}

                    target_result["directory"] = directory
                    target_result["target_url"] = url



                    crawl_results.append(target_result)

                    _log_provider_result(
                        provider_name=(
                            "bbb_native" if directory == "bbb" else directory
                        ),
                        status=str(target_result.get("status") or "success"),
                        records=int(target_result.get("records_found") or 0),
                        error=str(
                            target_result.get("access_reason")
                            or target_result.get("blocked_reason")
                            or ""
                        ),
                    )

                except Exception as exc:
                    _log_provider_result(
                        provider_name=(
                            "bbb_native" if directory == "bbb" else directory
                        ),
                        status="failed",
                        records=0,
                        error=str(exc),
                    )
                    crawl_results.append(
                        {
                            "architecture": directory,
                            "directory": directory,
                            "source_url": url,
                            "target_url": url,
                            "status": "failed",
                            "records_found": 0,
                            "reason": str(exc),
                            "category_map": {},
                            "service_map": {},
                        }
                    )

        elif execution_details.get("skipped"):
            crawl_results.extend(
                {
                    "architecture": skipped.get("directory", ""),
                    "directory": skipped.get("directory", ""),
                    "source_url": "",
                    "target_url": "",
                    "status": "not_supported",
                    "records_found": 0,
                    "reason": skipped.get("reason", ""),
                    "access_reason": skipped.get("detail", ""),
                    "category_map": {},
                    "service_map": {},
                }
                for skipped in execution_details["skipped"]
            )
        else:
            target_result = await run_crawler(
                input_data,
                enable_website_enrichment=enable_website_enrichment,
                website_timeout_ms=website_timeout_ms,
            ) or {}
            crawl_results.append(target_result)

        successful_architectures = [
            str(item.get("architecture") or item.get("directory") or "")
            for item in crawl_results
            if item
        ]
        source_urls = [
            str(item.get("source_url") or item.get("target_url") or "")
            for item in crawl_results
            if item
        ]
        primary_result = crawl_results[0] if crawl_results else {}

        crawl_info = {
            "architecture": (
                ", ".join(
                    dict.fromkeys(
                        value for value in successful_architectures if value
                    )
                )
                or ""
            ),
            "source_url": (
                " | ".join(
                    dict.fromkeys(value for value in source_urls if value)
                )
                or ""
            ),
            "directory_results": crawl_results,
            "category_map": {},
            "service_map": {},
            "status": primary_result.get("status", ""),
            "access_status": primary_result.get("access_status", ""),
            "access_reason": primary_result.get("access_reason", ""),
            "external_provider": primary_result.get("external_provider", {}),
        }

        dataset = await Actor.open_dataset()
        peek = await dataset.get_data(limit=3)
        peek_items = peek.items or []
        Actor.log.info(
            f"DATASET AFTER CRAWL count={len(peek_items)} "
            f"keys={list(peek_items[0].keys()) if peek_items else []}"
        )

        combined_category_map: dict[str, Any] = {}
        combined_service_map: dict[str, Any] = {}

        for result in crawl_results:
            combined_category_map.update(result.get("category_map", {}) or {})
            combined_service_map.update(result.get("service_map", {}) or {})

        crawl_info["category_map"] = combined_category_map
        crawl_info["service_map"] = combined_service_map

        automatic_categories = crawl_info.get("category_map", {}) or {}
        automatic_services = crawl_info.get("service_map", {}) or {}

        taxonomy = input_data.get("taxonomy", {}) or {}
        manual_categories = taxonomy.get("categoryMap", {}) or {}
        manual_services = taxonomy.get("serviceMap", {}) or {}

        category_map = {
            **_normalize_tax_map(RPC_CATEGORY_MAP),
            **_normalize_tax_map(automatic_categories),
            **_normalize_tax_map(manual_categories),
        }
        service_map = {
            **_normalize_tax_map(RSS_SERVICE_MAP),
            **_normalize_tax_map(automatic_services),
            **_normalize_tax_map(manual_services),
        }

        if input_data.get("debug"):
            Actor.log.info(
                f"DEBUG category_map sample={list(category_map.items())[:10]}"
            )
            Actor.log.info(
                f"DEBUG service_map sample={list(service_map.items())[:10]}"
            )

        await Actor.set_value(
            "TAXONOMY.json",
            {
                "source_url": start_url,
                "category_map": category_map,
                "service_map": service_map,
                "counts": {
                    "auto_categories": len(automatic_categories),
                    "auto_services": len(automatic_services),
                    "manual_categories": len(manual_categories),
                    "manual_services": len(manual_services),
                    "final_categories": len(category_map),
                    "final_services": len(service_map),
                },
            },
            content_type="application/json",
        )

        Actor.log.info("Starting dataset export to KV...")

        out_base = input_data.get("outputBaseName", "output")
        write_csv = bool(input_data.get("outputCsv", True))
        write_xlsx = bool(input_data.get("outputXlsx", False))
        columns_mode = input_data.get(
            "columnsMode",
            input_data.get("outputColumnsMode", "default"),
        )

        await export_dataset_to_kv(
            out_base=out_base,
            write_csv=write_csv,
            write_xlsx=write_xlsx,
            columns_mode=columns_mode,
        )

        final_dataset = await Actor.open_dataset()
        final_data = await final_dataset.get_data(limit=999999)
        final_items = [
            item
            for item in (final_data.items or [])
            if not (isinstance(item, dict) and item.get("_probe"))
        ]

        export_paths = {
            "csv": f"{out_base}.csv" if write_csv else "",
            "xlsx": f"{out_base}.xlsx" if write_xlsx else "",
        }

        print_run_summary(
            items=final_items,
            crawl_info=crawl_info,
            export_paths=export_paths,
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
