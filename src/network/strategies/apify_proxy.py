from __future__ import annotations

from typing import Any

from src.models.proxy_config import ProxyConfig
from src.network.proxy_strategy import ProxyStrategy


class ApifyProxyStrategy(ProxyStrategy):
    def __init__(
        self,
        proxy: ProxyConfig,
        debug: bool = False,
    ):
        self.proxy = proxy
        self.debug = debug

    def build_proxy_settings(self) -> dict[str, Any] | None:
        if self.debug:
            print(
                "DEBUG ApifyProxyStrategy: Apify proxy requested, "
                "real proxy URL integration will be added next."
            )

        return None
