from src.adapters.providers.base_provider import BaseProvider
from src.adapters.providers.bootstrap import build_provider_registry


class BootstrapProvider(BaseProvider):

    def provider_name(self) -> str:
        return "bootstrap-provider"

    def capabilities(self) -> dict[str, bool]:
        return {"search": True}

    def search(self, request):
        return []


def test_build_provider_registry():
    registry = build_provider_registry(
        [BootstrapProvider()]
    )

    assert registry.names() == ["bootstrap-provider"]
