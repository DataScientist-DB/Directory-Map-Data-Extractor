from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProxyConfig:
    """
    Universal proxy configuration for all adapters.
    """

    use_apify_proxy: bool = False
    proxy_groups: list[str] | None = None
    proxy_country: str = ""
    proxy_url: str = ""
    username: str = ""
    password: str = ""
    max_retries: int = 3
    request_delay: int = 1500
