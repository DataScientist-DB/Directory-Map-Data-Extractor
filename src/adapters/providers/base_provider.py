from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseProvider(ABC):
    """
    Common interface for all business-directory providers.

    Required provider methods:
        - provider_name()
        - capabilities()
        - search()

    Optional provider methods have safe default implementations.
    """

    @abstractmethod
    def provider_name(self) -> str:
        """Return a unique provider identifier."""
        raise NotImplementedError

    @abstractmethod
    def capabilities(self) -> Dict[str, bool]:
        """
        Return provider capabilities.

        Example:
            {
                "search": True,
                "details": True,
                "enrichment": False,
                "parallel_safe": False,
            }
        """
        raise NotImplementedError

    @abstractmethod
    def search(self, request: Any) -> Any:
        """Execute the provider search and return normalized records."""
        raise NotImplementedError

    def priority(self) -> int:
        """
        Lower values run first.

        Default priority is intentionally low-preference so providers can
        override it explicitly.
        """
        return 100

    def enabled(self) -> bool:
        """Return whether this provider may be selected."""
        return True

    def health(self) -> str:
        """
        Return provider health status.

        Suggested values:
            healthy
            degraded
            unavailable
            blocked
            unknown
        """
        return "unknown"

    def metadata(self) -> Dict[str, Any]:
        """Return optional provider information."""
        return {}

    def supports(self, capability: str) -> bool:
        """Return True when the provider supports the requested capability."""
        return bool(self.capabilities().get(capability, False))
