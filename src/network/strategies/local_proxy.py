from __future__ import annotations

from typing import Any

from src.network.proxy_strategy import ProxyStrategy


class LocalProxyStrategy(ProxyStrategy):
    async def build_proxy_settings(self) -> dict[str, Any] | None:
        return None
