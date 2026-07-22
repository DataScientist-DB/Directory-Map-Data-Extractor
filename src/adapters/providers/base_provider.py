from abc import ABC, abstractmethod

class BaseProvider(ABC):

    @abstractmethod
    def search(self, request):
        """Return normalized company records."""
        pass

    @abstractmethod
    def capabilities(self):
        """Return provider capabilities."""
        pass

    @abstractmethod
    def provider_name(self):
        """Return provider identifier."""
        pass
