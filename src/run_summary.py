from __future__ import annotations

from typing import Any


def count_non_empty(items: list[dict[str, Any]], field: str) -> int:
    return sum(1 for item in items if item.get(field))


def print_run_summary(
    items: list[dict[str, Any]],
    crawl_info: dict[str, Any],
    export_paths: dict[str, str] | None = None,
) -> None:
    export_paths = export_paths or {}

    architecture = crawl_info.get("architecture", "")
    source_url = crawl_info.get("source_url", "")
    records_found = len(items)

    print("\n" + "=" * 60)
    print(" UNIVERSAL BUSINESS DIRECTORY INTELLIGENCE")
    print(" RUN SUMMARY")
    print("=" * 60)

    print(f"Architecture............. {architecture}")
    print(f"Source URL............... {source_url}")
    print()
    print(f"Records exported......... {records_found}")
    print(f"Emails................... {count_non_empty(items, 'email')}")
    print(f"Phones................... {count_non_empty(items, 'phone')}")
    print(f"Websites................. {count_non_empty(items, 'website')}")
    print()
    print(f"Facebook................. {count_non_empty(items, 'facebook')}")
    print(f"LinkedIn................. {count_non_empty(items, 'linkedin')}")
    print(f"Instagram................ {count_non_empty(items, 'instagram')}")
    print(f"YouTube.................. {count_non_empty(items, 'youtube')}")
    print(f"Twitter.................. {count_non_empty(items, 'twitter')}")
    print()
    print(f"Website enrichment....... {count_non_empty(items, 'website_enrichment_status')}")
    print(f"CSV...................... {'✓' if export_paths.get('csv') else '-'}")
    print(f"XLSX..................... {'✓' if export_paths.get('xlsx') else '-'}")

    print("=" * 60 + "\n")