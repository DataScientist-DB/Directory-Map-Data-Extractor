from src.models.provider_report import ProviderReport
from src.models.provider_result import ProviderResult
from src.models.provider_status import ProviderStatus


def test_successful_provider_result() -> None:
    report = ProviderReport(
        directory="bbb",
        provider="native_bbb",
        status=ProviderStatus.SUCCESS.value,
    )

    result = ProviderResult(
        records=[
            {
                "entity_name": "Example Company",
            }
        ],
        report=report,
    )

    assert result.succeeded is True
    assert result.usable is True
    assert result.should_fallback is False
    assert result.report.records_found == 1


def test_blocked_provider_result_requires_fallback() -> None:
    report = ProviderReport(
        directory="bbb",
        provider="native_bbb",
        status=ProviderStatus.BLOCKED.value,
        reason="Cloudflare Turnstile",
    )

    result = ProviderResult(
        records=[],
        report=report,
    )

    assert result.succeeded is False
    assert result.usable is False
    assert result.should_fallback is True
    assert result.report.records_found == 0


def test_demo_provider_result_requires_fallback() -> None:
    report = ProviderReport(
        directory="bbb",
        provider="external_bbb",
        status=ProviderStatus.DEMO.value,
    )

    result = ProviderResult(
        records=[],
        report=report,
    )

    assert result.should_fallback is True


def test_provider_report_to_dict() -> None:
    report = ProviderReport(
        directory="chambermaster",
        provider="chambermaster_native",
        status=ProviderStatus.SUCCESS.value,
        records_found=5,
        duration_seconds=1.25,
    )

    payload = report.to_dict()

    assert payload["directory"] == "chambermaster"
    assert payload["provider"] == "chambermaster_native"
    assert payload["records_found"] == 5
    assert payload["duration_seconds"] == 1.25
