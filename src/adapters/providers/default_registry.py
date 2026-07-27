from typing import Any

from src.adapters.providers.bbb_crawlerbros import BBBCrawlerBrosProvider
from src.adapters.providers.bbb_native import BBBNativeProvider
from src.adapters.providers.bootstrap import build_provider_registry
from src.adapters.providers.chambermaster import ChamberMasterProvider
from src.adapters.providers.registry import ProviderRegistry


def build_default_provider_registry(
    input_data: dict[str, Any],
) -> ProviderRegistry:
    bbb_config = input_data.get("bbbProvider", {}) or {}

    providers = [
        BBBCrawlerBrosProvider(
            actor_id=bbb_config.get(
                "actorId",
                "ocrad/bbb-company-scraper",
            ),
            timeout_seconds=int(
                bbb_config.get(
                    "timeoutSeconds",
                    600,
                )
            ),
        ),
        BBBNativeProvider(),
        ChamberMasterProvider(),
    ]

    return build_provider_registry(providers)
