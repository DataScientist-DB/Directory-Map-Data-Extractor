from src.adapters.providers.base_provider import BaseProvider


class ExampleProvider(BaseProvider):

    def provider_name(self) -> str:
        return "example"

    def capabilities(self) -> dict[str, bool]:
        return {
            "search": True,
            "details": False,
            "enrichment": False,
            "parallel_safe": True,
        }

    def search(self, request):
        return [{"name": "Example Company"}]


def test_base_provider_defaults():
    provider = ExampleProvider()

    assert provider.provider_name() == "example"
    assert provider.priority() == 100
    assert provider.enabled() is True
    assert provider.health() == "unknown"
    assert provider.metadata() == {}


def test_base_provider_supports_capability():
    provider = ExampleProvider()

    assert provider.supports("search") is True
    assert provider.supports("details") is False
    assert provider.supports("unknown_capability") is False
