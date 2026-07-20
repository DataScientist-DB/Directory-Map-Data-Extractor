from src.models.provider_status import ProviderStatus


def test_provider_status_values() -> None:
    assert ProviderStatus.SUCCESS.value == "success"
    assert ProviderStatus.EMPTY.value == "empty"
    assert ProviderStatus.BLOCKED.value == "blocked"
    assert ProviderStatus.DEMO.value == "demo"
    assert ProviderStatus.RUNTIME_ERROR.value == "runtime_error"
