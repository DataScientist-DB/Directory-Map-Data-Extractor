from typing import Iterable

from src.adapters.providers.base_provider import BaseProvider
from src.adapters.providers.registry import ProviderRegistry


def build_provider_registry(
    providers: Iterable[BaseProvider],
) -> ProviderRegistry:
    """
    Build a registry from already constructed provider instances.

    Provider construction remains outside this function because individual
    providers may require configuration, clients, proxies, or credentials.
    """
    registry = ProviderRegistry()

    for provider in providers:
        registry.register(provider)

    return registry
