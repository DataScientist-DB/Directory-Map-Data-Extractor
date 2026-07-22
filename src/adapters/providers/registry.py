from typing import Dict, List, Optional

from src.adapters.providers.base_provider import BaseProvider


class ProviderRegistry:
    """
    Central registry for business-directory providers.

    Providers are identified by provider.provider_name().
    """

    def __init__(self) -> None:
        self._providers: Dict[str, BaseProvider] = {}

    def register(
        self,
        provider: BaseProvider,
        *,
        replace: bool = False,
    ) -> None:
        """
        Register a provider.

        Args:
            provider:
                Provider instance implementing BaseProvider.

            replace:
                Replace an existing provider with the same name.

        Raises:
            TypeError:
                When provider is not a BaseProvider instance.

            ValueError:
                When the name is empty or already registered.
        """
        if not isinstance(provider, BaseProvider):
            raise TypeError(
                "Provider must be an instance of BaseProvider."
            )

        name = provider.provider_name().strip()

        if not name:
            raise ValueError("Provider name cannot be empty.")

        if name in self._providers and not replace:
            raise ValueError(
                f"Provider '{name}' is already registered."
            )

        self._providers[name] = provider

    def unregister(self, name: str) -> Optional[BaseProvider]:
        """Remove and return a registered provider."""
        return self._providers.pop(name, None)

    def get(self, name: str) -> Optional[BaseProvider]:
        """Return a provider by name, or None when it is not registered."""
        return self._providers.get(name)

    def require(self, name: str) -> BaseProvider:
        """
        Return a provider by name.

        Raises KeyError when it does not exist.
        """
        provider = self.get(name)

        if provider is None:
            available = ", ".join(self.names()) or "none"
            raise KeyError(
                f"Provider '{name}' is not registered. "
                f"Available providers: {available}"
            )

        return provider

    def names(self) -> List[str]:
        """Return registered provider names in alphabetical order."""
        return sorted(self._providers.keys())

    def all(self) -> List[BaseProvider]:
        """Return all registered providers."""
        return list(self._providers.values())

    def enabled(self) -> List[BaseProvider]:
        """Return enabled providers ordered by priority."""
        providers = [
            provider
            for provider in self._providers.values()
            if provider.enabled()
        ]

        return sorted(
            providers,
            key=lambda provider: (
                provider.priority(),
                provider.provider_name(),
            ),
        )

    def by_capability(self, capability: str) -> List[BaseProvider]:
        """
        Return enabled providers that support a capability,
        ordered by priority.
        """
        return [
            provider
            for provider in self.enabled()
            if provider.supports(capability)
        ]

    def select(
        self,
        *,
        name: Optional[str] = None,
        capability: str = "search",
    ) -> BaseProvider:
        """
        Select one provider.

        When name is supplied, validate that provider directly.
        Otherwise select the highest-priority enabled provider supporting
        the requested capability.
        """
        if name:
            provider = self.require(name)

            if not provider.enabled():
                raise ValueError(
                    f"Provider '{name}' is disabled."
                )

            if not provider.supports(capability):
                raise ValueError(
                    f"Provider '{name}' does not support "
                    f"capability '{capability}'."
                )

            return provider

        candidates = self.by_capability(capability)

        if not candidates:
            raise LookupError(
                f"No enabled provider supports capability "
                f"'{capability}'."
            )

        return candidates[0]
