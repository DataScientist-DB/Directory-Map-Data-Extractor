from __future__ import annotations

from typing import Any


DIAGNOSTIC_STATUSES = {
    "blocked",
    "failed",
    "runtime_error",
    "authentication_failed",
    "rate_limited",
    "rental_required",
    "actor_unavailable",
    "input_error",
    "demo",
    "timeout",
    "network_error",
    "not_supported",
}


def count_non_empty(
    items: list[dict[str, Any]],
    field: str,
) -> int:
    return sum(
        1
        for item in items
        if item.get(field)
    )


def is_business_record(
    item: dict[str, Any],
) -> bool:
    status = str(
        item.get(
            "status",
            "",
        )
        or ""
    ).strip().lower()

    entity_name = str(
        item.get(
            "entity_name",
            "",
        )
        or ""
    ).strip()

    if not entity_name:
        return False

    if status in DIAGNOSTIC_STATUSES:
        return False

    access_status = str(
        item.get(
            "access_status",
            "",
        )
        or ""
    ).strip().lower()

    if access_status in DIAGNOSTIC_STATUSES:
        return False

    blocked_reason = str(
        item.get(
            "blocked_reason",
            "",
        )
        or ""
    ).strip()

    if blocked_reason:
        return False

    return True


def split_records(
    items: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    business_items = [
        item
        for item in items
        if is_business_record(item)
    ]

    diagnostic_items = [
        item
        for item in items
        if not is_business_record(item)
    ]

    return business_items, diagnostic_items


def get_intelligence_scores(
    items: list[dict[str, Any]],
) -> list[int]:
    scores: list[int] = []

    for item in items:
        value = item.get(
            "intelligence_score"
        )

        if value is None or value == "":
            continue

        try:
            scores.append(
                int(value)
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

    return scores


def print_intelligence_summary(
    items: list[dict[str, Any]],
) -> None:
    scores = get_intelligence_scores(
        items
    )

    if not scores:
        print(
            "Business intelligence.... -"
        )
        return

    average_score = (
        sum(scores)
        / len(scores)
    )

    excellent = sum(
        1
        for score in scores
        if score >= 90
    )

    good = sum(
        1
        for score in scores
        if 70 <= score < 90
    )

    fair = sum(
        1
        for score in scores
        if 50 <= score < 70
    )

    poor = sum(
        1
        for score in scores
        if 30 <= score < 50
    )

    very_poor = sum(
        1
        for score in scores
        if score < 30
    )

    print(
        "Business intelligence.... ✓"
    )
    print(
        f"Average BI score......... "
        f"{average_score:.1f}"
    )
    print(
        f"Excellent................ "
        f"{excellent}"
    )
    print(
        f"Good..................... "
        f"{good}"
    )
    print(
        f"Fair..................... "
        f"{fair}"
    )
    print(
        f"Poor..................... "
        f"{poor}"
    )
    print(
        f"Very poor................ "
        f"{very_poor}"
    )


def get_native_provider_status(
    items: list[dict[str, Any]],
    crawl_info: dict[str, Any],
) -> str:
    for item in items:
        blocked_reason = str(
            item.get("blocked_reason", "")
            or item.get("access_reason", "")
            or ""
        ).strip()

        access_status = str(
            item.get("access_status", "")
            or ""
        ).strip().lower()

        if blocked_reason:
            return "blocked"

        if access_status in DIAGNOSTIC_STATUSES:
            return access_status

    blocked_reason = str(
        crawl_info.get("blocked_reason", "")
        or crawl_info.get("access_reason", "")
        or ""
    ).strip()

    access_status = str(
        crawl_info.get("access_status", "")
        or ""
    ).strip().lower()

    general_status = str(
        crawl_info.get("status", "")
        or ""
    ).strip().lower()

    if blocked_reason:
        return "blocked"

    if access_status in DIAGNOSTIC_STATUSES:
        return access_status

    if general_status in DIAGNOSTIC_STATUSES:
        return general_status

    if access_status:
        return access_status

    if general_status == "adapter_extraction_complete":
        return "completed"

    return general_status

def print_provider_summary(
    items: list[dict[str, Any]],
    crawl_info: dict[str, Any],
) -> None:

    architecture = str(
        crawl_info.get(
            "architecture",
            "",
        )
    ).strip().lower()

    if architecture != "bbb":
        return

    external_report = crawl_info.get(
        "external_provider",
        {},
    )

    if not isinstance(
        external_report,
        dict,
    ):
        external_report = {}

    external_status = str(
        external_report.get(
            "status",
            "",
        )
        or ""
    ).strip().lower()

    native_status = get_native_provider_status(
        items=items,
        crawl_info=crawl_info,
    )

    business_items, diagnostic_items = (
        split_records(items)
    )

    if business_items:
        final_outcome = "success"
    elif diagnostic_items:
        final_outcome = "diagnostic"
    elif (
        external_status
        or native_status
    ):
        final_outcome = "empty"
    else:
        final_outcome = "unknown"

    if (
        not external_status
        and not native_status
    ):
        return

    print("Provider summary")
    print("-" * 60)

    if external_status:
        print(
            "BBB External............ "
            f"{external_status}"
        )

    if native_status:
        print(
            "BBB Native.............. "
            f"{native_status}"
        )

    print(
        "Final BBB outcome........ "
        f"{final_outcome}"
    )
    print()


def print_run_summary(
    items: list[dict[str, Any]],
    crawl_info: dict[str, Any],
    export_paths: dict[str, str] | None = None,
) -> None:
    export_paths = (
        export_paths
        or {}
    )

    architecture = str(
        crawl_info.get(
            "architecture",
            "",
        )
        or ""
    ).strip()

    source_url = str(
        crawl_info.get(
            "source_url",
            "",
        )
        or ""
    ).strip()

    business_items, diagnostic_items = (
        split_records(items)
    )

    businesses_found = len(
        business_items
    )

    diagnostics_found = len(
        diagnostic_items
    )

    total_records = len(
        items
    )

    print(
        "\n"
        + "=" * 60
    )
    print(
        " UNIVERSAL BUSINESS DIRECTORY INTELLIGENCE"
    )
    print(
        " RUN SUMMARY"
    )
    print(
        "=" * 60
    )

    print(
        f"Architecture............. "
        f"{architecture}"
    )

    print(
        f"Source URL............... "
        f"{source_url}"
    )

    print()

    print_provider_summary(
        items=items,
        crawl_info=crawl_info,
    )

    print(
        f"Businesses exported...... "
        f"{businesses_found}"
    )

    print(
        f"Diagnostic records....... "
        f"{diagnostics_found}"
    )

    print(
        f"Total records............ "
        f"{total_records}"
    )

    print(
        f"Emails................... "
        f"{count_non_empty(business_items, 'email')}"
    )

    print(
        f"Phones................... "
        f"{count_non_empty(business_items, 'phone')}"
    )

    print(
        f"Websites................. "
        f"{count_non_empty(business_items, 'website')}"
    )

    print()

    print(
        f"Facebook................. "
        f"{count_non_empty(business_items, 'facebook')}"
    )

    print(
        f"LinkedIn................. "
        f"{count_non_empty(business_items, 'linkedin')}"
    )

    print(
        f"Instagram................ "
        f"{count_non_empty(business_items, 'instagram')}"
    )

    print(
        f"YouTube.................. "
        f"{count_non_empty(business_items, 'youtube')}"
    )

    print(
        f"Twitter.................. "
        f"{count_non_empty(business_items, 'twitter')}"
    )

    print()

    print(
        f"Website enrichment....... "
        f"{count_non_empty(business_items, 'website_enrichment_status')}"
    )

    print_intelligence_summary(
        business_items
    )

    print()

    print(
        f"CSV...................... "
        f"{'✓' if export_paths.get('csv') else '-'}"
    )

    print(
        f"XLSX..................... "
        f"{'✓' if export_paths.get('xlsx') else '-'}"
    )

    print(
        "=" * 60
        + "\n"
    )
