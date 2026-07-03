from __future__ import annotations

from src.adapters.registry import (
    list_adapters,
    create_adapter,
)


def test_registry():
    print("\n===== Adapter Registry Smoke Test =====")

    adapters = list_adapters()

    print(f"Registered adapters: {adapters}")

    for key in adapters:
        adapter = create_adapter(
            key,
            source_url="https://example.com",
            debug=False,
        )

        print(f"\nAdapter: {key}")
        print(f"  Name: {adapter.info.name}")
        print(f"  Version: {adapter.info.version}")
        print(f"  Description: {adapter.info.description}")
        print(f"  Search: {adapter.capabilities.search}")
        print(f"  Pagination: {adapter.capabilities.pagination}")
        print(f"  Contact Details: {adapter.capabilities.contact_details}")

    print("\nRegistry smoke test PASSED")


if __name__ == "__main__":
    test_registry()
