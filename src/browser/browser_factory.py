from __future__ import annotations

from typing import Any

from playwright.async_api import Browser, Playwright

from src.models.proxy_config import ProxyConfig


class BrowserFactory:
    """
    Central browser launcher for UBDIP.

    Handles:
    - local browser launch
    - custom proxy URL
    - Apify proxy awareness
    - headless/headful mode
    """

    def __init__(
        self,
        proxy: ProxyConfig | None = None,
        headless: bool = True,
        debug: bool = False,
    ) -> None:
        self.proxy = proxy or ProxyConfig()
        self.headless = headless
        self.debug = debug

    def build_playwright_proxy(self) -> dict[str, str] | None:
        if self.proxy.proxy_url:
            result = {"server": self.proxy.proxy_url}

            if self.proxy.username:
                result["username"] = self.proxy.username

            if self.proxy.password:
                result["password"] = self.proxy.password

            return result

        return None

    def build_launch_options(self) -> dict[str, Any]:
        launch_options: dict[str, Any] = {
            "headless": self.headless,
            "args": [
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        }

        playwright_proxy = self.build_playwright_proxy()

        if playwright_proxy:
            launch_options["proxy"] = playwright_proxy

            if self.debug:
                print("DEBUG BrowserFactory using custom proxy URL")

        elif self.proxy.use_apify_proxy and self.debug:
            print(
                "DEBUG BrowserFactory: Apify proxy requested, "
                "but Apify proxy URL must be provided by Actor proxy integration."
            )

        return launch_options

    async def launch(self, playwright: Playwright) -> Browser:
        launch_options = self.build_launch_options()
        return await playwright.chromium.launch(**launch_options)
