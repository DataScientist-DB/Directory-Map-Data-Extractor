from __future__ import annotations

from typing import Any

from src.adapters.base import BaseDirectoryAdapter
from src.adapters.bbb import BBBAdapter
from src.adapters.chambermaster import ChamberMasterAdapter
from src.adapters.models import AdapterCapabilities, AdapterInfo
from src.adapters.yelp import YelpAdapter


DIRECTORY_REGISTRY: dict[str, type[BaseDirectoryAdapter]] = {
    "chambermaster": ChamberMasterAdapter,
    "bbb": BBBAdapter,
    "yelp": YelpAdapter,
}


def normalize_adapter_key(key: str) -> str:
    return (key or "").strip().lower()


def list_adapters() -> list[str]:
    return sorted(DIRECTORY_REGISTRY.keys())


def adapter_exists(key: str) -> bool:
    return normalize_adapter_key(key) in DIRECTORY_REGISTRY


def get_adapter_class(key: str) -> type[BaseDirectoryAdapter]:
    normalized_key = normalize_adapter_key(key)

    if normalized_key not in DIRECTORY_REGISTRY:
        supported = ", ".join(list_adapters())
        raise ValueError(
            f"Unsupported directory adapter: {key!r}. "
            f"Supported adapters: {supported}"
        )

    return DIRECTORY_REGISTRY[normalized_key]


def create_adapter(
    key: str,
    source_url: str = "",
    debug: bool = False,
    config: dict[str, Any] | None = None,
    **kwargs: Any,
) -> BaseDirectoryAdapter:
    adapter_class = get_adapter_class(key)

    return adapter_class(
        source_url=source_url,
        debug=debug,
        config=config,
        **kwargs,
    )


def get_adapter_info(key: str) -> AdapterInfo:
    adapter_class = get_adapter_class(key)
    return adapter_class.INFO


def get_adapter_capabilities(key: str) -> AdapterCapabilities:
    adapter_class = get_adapter_class(key)
    return adapter_class.CAPABILITIES


def get_registry_summary() -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []

    for key in list_adapters():
        info = get_adapter_info(key)
        capabilities = get_adapter_capabilities(key)

        summary.append(
            {
                "key": key,
                "name": info.name,
                "version": info.version,
                "description": info.description,
                "capabilities": capabilities.__dict__,
            }
        )

    return summary
