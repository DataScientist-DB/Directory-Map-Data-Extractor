from __future__ import annotations

from typing import Any

from playwright.async_api import Browser, Playwright

from src.models.proxy_config import ProxyConfig
from src.network.proxy_manager import ProxyManager


class BrowserFactory:
    """
    Central browser launcher for UBDIP.

    Responsibilities:
    - Launch Playwright browsers
    - Configure headless/headful mode
    - Delegate proxy configuration to ProxyManager
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

    async def build_launch_options(self) -> dict[str, Any]:
        """
        Build Playwright launch options.
        """

        launch_options: dict[str, Any] = {
            "headless": self.headless,
            "args": [
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        }

        proxy_manager = ProxyManager(
            proxy=self.proxy,
            debug=self.debug,
        )

        playwright_proxy = await proxy_manager.build_proxy_settings()

        if playwright_proxy:
            launch_options["proxy"] = playwright_proxy

            if self.debug:
                print("DEBUG BrowserFactory using proxy")

        elif self.proxy.use_apify_proxy:
            if self.debug:
                print(
                    "DEBUG BrowserFactory waiting for Apify proxy integration"
                )

        return launch_options

    async def launch(
        self,
        playwright: Playwright,
    ) -> Browser:
        """
        Launch a Playwright Chromium browser.
        """

        launch_options = await self.build_launch_options()

        return await playwright.chromium.launch(
            **launch_options,
        )
