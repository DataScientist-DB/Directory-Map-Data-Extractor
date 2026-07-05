from __future__ import annotations

from typing import Any

from src.models.proxy_config import ProxyConfig
from src.network.proxy_strategy import ProxyStrategy
from src.network.strategies.apify_proxy import ApifyProxyStrategy
from src.network.strategies.custom_proxy import CustomProxyStrategy
from src.network.strategies.local_proxy import LocalProxyStrategy


class ProxyManager:
    def __init__(
        self,
        proxy: ProxyConfig | None = None,
        debug: bool = False,
    ):
        self.proxy = proxy or ProxyConfig()
        self.debug = debug

    def _select_strategy(self) -> ProxyStrategy:
        if self.proxy.proxy_url:
            return CustomProxyStrategy(self.proxy)

        if self.proxy.use_apify_proxy:
            return ApifyProxyStrategy(
                proxy=self.proxy,
                debug=self.debug,
            )

        return LocalProxyStrategy()

    def build_proxy_settings(self) -> dict[str, Any] | None:
        strategy = self._select_strategy()
        return strategy.build_proxy_settings()

    # Backward-compatible alias during transition
    def playwright_proxy(self) -> dict[str, Any] | None:
        return self.build_proxy_settings()
