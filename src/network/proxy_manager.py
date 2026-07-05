from __future__ import annotations

from typing import Any

from src.models.proxy_config import ProxyConfig


class ProxyManager:
    """
    Builds Playwright proxy settings from ProxyConfig.

    Future versions will support:

    - Apify Residential Proxy
    - Proxy rotation
    - Country selection
    - Automatic fallback
    - Health checks
    """

    def __init__(
        self,
        proxy: ProxyConfig | None = None,
        debug: bool = False,
    ):
        self.proxy = proxy or ProxyConfig()
        self.debug = debug

    def playwright_proxy(self) -> dict[str, Any] | None:

        if self.proxy.proxy_url:

            result = {
                "server": self.proxy.proxy_url,
            }

            if self.proxy.username:
                result["username"] = self.proxy.username

            if self.proxy.password:
                result["password"] = self.proxy.password

            return result

        if self.proxy.use_apify_proxy:

            if self.debug:
                print(
                    "DEBUG ProxyManager: "
                    "Apify Residential Proxy requested."
                )

            # RC1.4.4
            # Here we will request the proxy URL
            # from the Apify SDK.

        return None
