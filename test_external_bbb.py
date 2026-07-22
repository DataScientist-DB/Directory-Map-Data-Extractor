import json
import os
import sys
from typing import Any

from apify_client import ApifyClient


ACTOR_ID = "crawlerbros/bbb-scraper"

RUN_INPUT: dict[str, Any] = {
    "search": "traffic engineers",
    "location": "Irvine, CA",
    "maxResults": 10,
}


def main() -> int:
    token = os.getenv("APIFY_TOKEN")

    if not token:
        print("ERROR: APIFY_TOKEN is not defined.")
        return 1

    client = ApifyClient(token)

    try:
        print(f"Checking Actor: {ACTOR_ID}")

        actor_info = client.actor(ACTOR_ID).get()

        if not actor_info:
            print("ERROR: Actor could not be retrieved.")
            return 2

        print(
            "Actor found:",
            actor_info.get("username"),
            actor_info.get("name"),
        )

        print("\nStarting Actor with input:")
        print(json.dumps(RUN_INPUT, indent=2))

        run = client.actor(ACTOR_ID).call(
            run_input=RUN_INPUT,
            timeout_secs=300,
        )

        if not run:
            print("ERROR: Actor returned no run object.")
            return 3

        print("\nRun information:")
        print("ID:", run.get("id"))
        print("Status:", run.get("status"))
        print("Exit code:", run.get("exitCode"))
        print("Dataset ID:", run.get("defaultDatasetId"))

        dataset_id = run.get("defaultDatasetId")

        if not dataset_id:
            print("ERROR: Run has no default dataset.")
            return 4

        result = client.dataset(dataset_id).list_items(
            clean=True,
            limit=20,
        )

        records = result.items

        print(f"\nDataset records: {len(records)}")

        if records:
            print("\nCLASSIFICATION: EXTERNAL_SUCCESS_WITH_RECORDS")

            print("\nFirst record:")
            print(json.dumps(records[0], indent=2, default=str))

            with open(
                "external_bbb_sample.json",
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(records, file, indent=2, default=str)

            print("\nSaved: external_bbb_sample.json")
            return 0

        status_message = str(run.get("statusMessage") or "")
        status_message_lower = status_message.lower()

        print("\nDataset is empty.")

        if status_message:
            print("Status message:", status_message)

        failure_indicators = (
            "0 succeeded",
            "requestsfailed",
            "request failed",
            "blocked",
            "403",
        )

        if any(
            indicator in status_message_lower
            for indicator in failure_indicators
        ):
            print("\nCLASSIFICATION: EXTERNAL_PROVIDER_BLOCKED")
            return 6

        print("\nCLASSIFICATION: EXTERNAL_SUCCESS_EMPTY")
        return 5

    except Exception as exc:
        print(f"\nEXTERNAL BBB TEST FAILED: {type(exc).__name__}")
        print(str(exc))
        return 10


if __name__ == "__main__":
    sys.exit(main())
