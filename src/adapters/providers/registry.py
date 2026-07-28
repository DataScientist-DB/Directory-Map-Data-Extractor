from __future__ import annotations

from typing import Iterable, Optional

from src.adapters.providers.base_provider import BaseProvider


class ProviderRegistry:
    """Central registry with provider-name and directory-name resolution."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}

    @staticmethod
    def _normalize(value: str) -> str:
        return value.strip().casefold()

    def register(
        self,
        provider: BaseProvider,
        *,
        replace: bool = False,
    ) -> None:
        if not isinstance(provider, BaseProvider):
            raise TypeError("Provider must be an instance of BaseProvider.")

        name = self._normalize(provider.provider_name())
        if not name:
            raise ValueError("Provider name cannot be empty.")
        if name in self._providers and not replace:
            raise ValueError(f"Provider '{name}' is already registered.")
        self._providers[name] = provider

    def unregister(self, name: str) -> Optional[BaseProvider]:
        return self._providers.pop(self._normalize(name), None)

    def get(self, name: str) -> Optional[BaseProvider]:
        return self._providers.get(self._normalize(name))

    def require(self, name: str) -> BaseProvider:
        provider = self.get(name)
        if provider is None:
            available = ", ".join(self.names()) or "none"
            raise KeyError(
                f"Provider '{name}' is not registered. "
                f"Available providers: {available}"
            )
        return provider

    def names(self) -> list[str]:
        return sorted(self._providers)

    def all(self) -> list[BaseProvider]:
        return list(self._providers.values())

    def enabled(self) -> list[BaseProvider]:
        return sorted(
            (
                provider
                for provider in self._providers.values()
                if provider.enabled()
            ),
            key=lambda provider: (
                provider.priority(),
                provider.provider_name(),
            ),
        )

    def by_capability(self, capability: str) -> list[BaseProvider]:
        return [
            provider
            for provider in self.enabled()
            if provider.supports(capability)
        ]

    @staticmethod
    def _provider_directory(provider: BaseProvider) -> str:
        metadata = provider.metadata() or {}
        directory = str(metadata.get("directory") or "").strip()
        return directory or provider.provider_name()

    def directory_names(
        self,
        *,
        capability: str = "search",
    ) -> set[str]:
        """Return executable directory IDs exposed by enabled providers."""
        return {
            self._normalize(self._provider_directory(provider))
            for provider in self.by_capability(capability)
        }

    def providers_for_directory(
        self,
        directory: str,
        *,
        capability: str = "search",
    ) -> list[BaseProvider]:
        requested = self._normalize(directory)
        return [
            provider
            for provider in self.by_capability(capability)
            if (
                self._normalize(provider.provider_name()) == requested
                or self._normalize(
                    self._provider_directory(provider)
                ) == requested
            )
        ]

    def has_directory(
        self,
        directory: str,
        *,
        capability: str = "search",
    ) -> bool:
        return bool(
            self.providers_for_directory(
                directory,
                capability=capability,
            )
        )

    def select_for_directory(
        self,
        directory: str,
        *,
        capability: str = "search",
    ) -> BaseProvider:
        candidates = self.providers_for_directory(
            directory,
            capability=capability,
        )
        if not candidates:
            raise LookupError(
                f"No enabled provider for directory '{directory}' "
                f"supports capability '{capability}'."
            )
        return candidates[0]

    def select(
        self,
        *,
        name: Optional[str] = None,
        capability: str = "search",
    ) -> BaseProvider:
        if name:
            direct = self.get(name)
            if direct is None:
                return self.select_for_directory(
                    name,
                    capability=capability,
                )
            if not direct.enabled():
                raise ValueError(f"Provider '{name}' is disabled.")
            if not direct.supports(capability):
                raise ValueError(
                    f"Provider '{name}' does not support "
                    f"capability '{capability}'."
                )
            return direct

        candidates = self.by_capability(capability)
        if not candidates:
            raise LookupError(
                f"No enabled provider supports capability '{capability}'."
            )
        return candidates[0]
