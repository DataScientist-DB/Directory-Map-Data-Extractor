import json
import sys

from src.adapters.native_bbb_browser import (
    run_native_bbb_search_sync,
)


def main() -> int:
    result = run_native_bbb_search_sync(
        keyword="traffic engineers",
        location="Irvine, CA",
        max_profiles=10,
        headless=False,
    )

    payload = result.to_dict()

    print("\n===== NATIVE BBB BROWSER TEST =====")
    print(json.dumps(payload, indent=2, default=str))

    with open(
        "native_bbb_access_result.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            payload,
            file,
            indent=2,
            default=str,
        )

    print("\nSaved: native_bbb_access_result.json")

    if result.status == "success":
        print(
            f"\nSUCCESS: Found {result.profiles_found} BBB profiles."
        )
        return 0

    if result.status == "success_empty":
        print("\nSUCCESS_EMPTY: BBB opened but no profiles were found.")
        return 5

    if result.status == "blocked":
        print(
            f"\nBLOCKED: {result.blocked_reason}"
        )
        return 6

    print(
        f"\nFAILED: {result.blocked_reason}"
    )
    return 10


if __name__ == "__main__":
    sys.exit(main())
