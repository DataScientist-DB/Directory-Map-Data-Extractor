from __future__ import annotations

from typing import Any

from src.models.proxy_config import ProxyConfig
from src.network.proxy_strategy import ProxyStrategy


class CustomProxyStrategy(ProxyStrategy):
    def __init__(self, proxy: ProxyConfig):
        self.proxy = proxy

    def build_proxy_settings(self) -> dict[str, Any] | None:
        if not self.proxy.proxy_url:
            return None

        settings: dict[str, Any] = {"server": self.proxy.proxy_url}

        if self.proxy.username:
            settings["username"] = self.proxy.username

        if self.proxy.password:
            settings["password"] = self.proxy.password

        return settings
