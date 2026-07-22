from __future__ import annotations

from typing import Any

from src.adapters.base import BaseDirectoryAdapter
from src.adapters.registry import (
    adapter_exists,
    create_adapter,
    get_adapter_capabilities,
    get_adapter_info,
    list_adapters,
)


def normalize_architecture(value: str) -> str:
    return (value or "").strip().lower()


def get_adapter(
    architecture: str,
    source_url: str = "",
    debug: bool = False,
    config: dict[str, Any] | None = None,
    **kwargs: Any,
) -> BaseDirectoryAdapter | None:
    architecture = normalize_architecture(architecture)

    if not architecture:
        return None

    if not adapter_exists(architecture):
        return None

    return create_adapter(
        architecture,
        source_url=source_url,
        debug=debug,
        config=config,
        **kwargs,
    )


def require_adapter(
    architecture: str,
    source_url: str = "",
    debug: bool = False,
    config: dict[str, Any] | None = None,
    **kwargs: Any,
) -> BaseDirectoryAdapter:
    adapter = get_adapter(
        architecture=architecture,
        source_url=source_url,
        debug=debug,
        config=config,
        **kwargs,
    )

    if adapter is None:
        supported = ", ".join(list_adapters())
        raise ValueError(
            f"Unsupported or missing adapter architecture: {architecture!r}. "
            f"Supported adapters: {supported}"
        )

    return adapter


def get_adapter_metadata(architecture: str) -> dict[str, Any] | None:
    architecture = normalize_architecture(architecture)

    if not adapter_exists(architecture):
        return None

    info = get_adapter_info(architecture)
    capabilities = get_adapter_capabilities(architecture)

    return {
        "key": info.key,
        "name": info.name,
        "version": info.version,
        "author": info.author,
        "website": info.website,
        "description": info.description,
        "capabilities": capabilities.__dict__,
    }


def get_supported_adapters() -> list[str]:
    return list_adapters()
