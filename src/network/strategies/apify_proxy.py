from __future__ import annotations

from typing import Any

from apify import Actor

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

    async def build_proxy_settings(self) -> dict[str, Any] | None:
        actor_proxy_input: dict[str, Any] = {
            "useApifyProxy": True,
        }

        if self.proxy.proxy_groups:
            actor_proxy_input["apifyProxyGroups"] = self.proxy.proxy_groups

        if self.proxy.proxy_country:
            actor_proxy_input["apifyProxyCountry"] = self.proxy.proxy_country

        try:
            proxy_configuration = await Actor.create_proxy_configuration(
                actor_proxy_input=actor_proxy_input,
            )

            if not proxy_configuration:
                if self.debug:
                    print("DEBUG ApifyProxyStrategy: proxy configuration not available.")
                return None

            proxy_url = await proxy_configuration.new_url()

            if self.debug:
                print("DEBUG ApifyProxyStrategy: Apify proxy URL created.")

            return {"server": proxy_url}

        except Exception as e:
            if self.debug:
                print(
                    "DEBUG ApifyProxyStrategy: failed to create Apify proxy:",
                    repr(e),
                )

            return None
