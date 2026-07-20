from __future__ import annotations

import asyncio
import os
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import quote_plus

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)


@dataclass
class BBBAccessResult:
    status: str
    source_url: str
    http_status: int | None
    blocked_reason: str
    pages_visited: int
    profiles_found: int
    profile_urls: list[str]
    records: list[dict[str, Any]]
    provider: str = "native_bbb_browser"
    architecture: str = "bbb"
    access_strategy: str = "playwright"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class NativeBBBBrowserProvider:
    """
    Browser-based BBB discovery provider.

    This provider does not attempt to solve or bypass CAPTCHA challenges.
    It detects access restrictions and returns a diagnostic result so that
    UBDIP can continue safely with another provider or export diagnostics.
    """

    CHALLENGE_PATTERNS = (
        "cf-chl-",
        "challenge-platform",
        "challenges.cloudflare.com",
        "turnstile",
        "verify you are human",
        "checking your browser",
        "just a moment",
        "attention required",
    )

    PROFILE_PATH_MARKER = "/profile/"

    def __init__(
        self,
        *,
        headless: bool = True,
        navigation_timeout_ms: int = 45_000,
        request_delay_ms: int = 1_500,
    ) -> None:
        self.headless = headless
        self.navigation_timeout_ms = navigation_timeout_ms
        self.request_delay_ms = request_delay_ms

        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def __aenter__(self) -> "NativeBBBBrowserProvider":
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: object,
        exc: BaseException | None,
        traceback: object,
    ) -> None:
        await self.close()

    async def start(self) -> None:
        if self._context is not None:
            return

        self._playwright = await async_playwright().start()

        launch_options: dict[str, Any] = {
            "headless": self.headless,
        }

        proxy = self._build_proxy_configuration()
        if proxy:
            launch_options["proxy"] = proxy

        self._browser = await self._playwright.chromium.launch(
            **launch_options,
        )

        self._context = await self._browser.new_context(
            locale="en-US",
            timezone_id="America/Los_Angeles",
            viewport={"width": 1440, "height": 1000},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/150.0.0.0 Safari/537.36"
            ),
        )

        self._context.set_default_timeout(
            self.navigation_timeout_ms,
        )

        self._context.set_default_navigation_timeout(
            self.navigation_timeout_ms,
        )

    async def close(self) -> None:
        if self._context is not None:
            await self._context.close()
            self._context = None

        if self._browser is not None:
            await self._browser.close()
            self._browser = None

        if self._playwright is not None:
            await self._playwright.stop()
            self._playwright = None

    async def search(
        self,
        *,
        keyword: str,
        location: str,
        max_profiles: int = 25,
    ) -> BBBAccessResult:
        await self.start()

        if self._context is None:
            raise RuntimeError("BBB browser context was not initialized.")

        search_url = self.build_search_url(
            keyword=keyword,
            location=location,
        )

        page = await self._context.new_page()

        try:
            response = await page.goto(
                search_url,
                wait_until="domcontentloaded",
            )

            await page.wait_for_timeout(self.request_delay_ms)

            http_status = response.status if response else None

            blocked_reason = await self.detect_blocked_reason(
                page=page,
                http_status=http_status,
            )

            if blocked_reason:
                try:
                    await page.screenshot(
                        path="native_bbb_blocked.png",
                        full_page=True,
                    )
                except Exception as exc:
                    print(f"Could not save BBB screenshot: {exc}")

                try:
                    html = await page.content()

                    with open(
                        "native_bbb_blocked.html",
                        "w",
                        encoding="utf-8",
                    ) as file:
                        file.write(html)

                except Exception as exc:
                    print(f"Could not save BBB HTML: {exc}")

                return BBBAccessResult(
                    status="blocked",
                    source_url=search_url,
                    http_status=http_status,
                    blocked_reason=blocked_reason,
                    pages_visited=1,
                    profiles_found=0,
                    profile_urls=[],
                    records=[],
                )

            profile_urls = await self.extract_profile_urls(
                page=page,
                max_profiles=max_profiles,
            )

            if not profile_urls:
                return BBBAccessResult(
                    status="success_empty",
                    source_url=search_url,
                    http_status=http_status,
                    blocked_reason="",
                    pages_visited=1,
                    profiles_found=0,
                    profile_urls=[],
                    records=[],
                )

            records = [
                {
                    "source": "BBB",
                    "source_provider": "native_bbb_browser",
                    "source_url": url,
                    "bbb_profile_url": url,
                    "profile_url": url,
                    "discovery_status": "profile_discovered",
                }
                for url in profile_urls
            ]

            return BBBAccessResult(
                status="success",
                source_url=search_url,
                http_status=http_status,
                blocked_reason="",
                pages_visited=1,
                profiles_found=len(profile_urls),
                profile_urls=profile_urls,
                records=records,
            )

        except Exception as exc:
            return BBBAccessResult(
                status="runtime_error",
                source_url=search_url,
                http_status=None,
                blocked_reason=f"{type(exc).__name__}: {exc}",
                pages_visited=1,
                profiles_found=0,
                profile_urls=[],
                records=[],
            )

        finally:
            await page.close()



    @staticmethod
    def build_search_url(
        *,
        keyword: str,
        location: str,
    ) -> str:
        encoded_keyword = quote_plus(keyword.strip())
        encoded_location = quote_plus(location.strip())

        return (
            "https://www.bbb.org/search"
            f"?find_text={encoded_keyword}"
            f"&find_loc={encoded_location}"
            "&sort=Relevance"
        )

    async def detect_blocked_reason(
        self,
        *,
        page: Page,
        http_status: int | None,
    ) -> str:
        title = ""

        try:
            title = (await page.title()).strip().lower()
        except Exception:
            pass

        try:
            body_text = (
                await page.locator("body").inner_text(timeout=5_000)
            ).lower()
        except Exception:
            body_text = ""

        try:
            html = (await page.content()).lower()
        except Exception:
            html = ""

        combined = "\n".join(
            (
                title,
                body_text,
                html,
            )
        )

        if (
            "turnstile" in combined
            or "challenges.cloudflare.com" in combined
        ):
            return "Cloudflare Turnstile"

        if (
            "cloudflare" in combined
            or "cf-chl-" in combined
            or "challenge-platform" in combined
        ):
            return "Cloudflare challenge"

        if "verify you are human" in combined:
            return "Human verification challenge"

        if "checking your browser" in combined:
            return "Browser verification challenge"

        if "just a moment" in combined:
            return "Cloudflare interstitial"

        if http_status == 403:
            return "HTTP 403 access denied"

        if http_status == 429:
            return "HTTP 429 rate limited"

        if http_status == 401:
            return "HTTP 401 unauthorized"

        return ""

    async def extract_profile_urls(
        self,
        *,
        page: Page,
        max_profiles: int,
    ) -> list[str]:
        raw_urls = await page.locator(
            'a[href*="/profile/"]'
        ).evaluate_all(
            """
            elements => elements.map(element => element.href)
            """
        )

        unique_urls: list[str] = []
        seen: set[str] = set()

        for value in raw_urls:
            url = str(value or "").strip()

            if not url:
                continue

            if self.PROFILE_PATH_MARKER not in url:
                continue

            normalized = url.split("?")[0].rstrip("/")

            if normalized in seen:
                continue

            seen.add(normalized)
            unique_urls.append(normalized)

            if len(unique_urls) >= max_profiles:
                break

        return unique_urls

    @staticmethod
    def _build_proxy_configuration() -> dict[str, str] | None:
        server = os.getenv("BBB_PROXY_SERVER", "").strip()

        if not server:
            return None

        proxy: dict[str, str] = {
            "server": server,
        }

        username = os.getenv("BBB_PROXY_USERNAME", "").strip()
        password = os.getenv("BBB_PROXY_PASSWORD", "").strip()

        if username:
            proxy["username"] = username

        if password:
            proxy["password"] = password

        return proxy


async def run_native_bbb_search(
    *,
    keyword: str,
    location: str,
    max_profiles: int = 25,
    headless: bool = True,
) -> BBBAccessResult:
    async with NativeBBBBrowserProvider(
        headless=headless,
    ) as provider:
        return await provider.search(
            keyword=keyword,
            location=location,
            max_profiles=max_profiles,
        )


def run_native_bbb_search_sync(
    *,
    keyword: str,
    location: str,
    max_profiles: int = 25,
    headless: bool = True,
) -> BBBAccessResult:
    return asyncio.run(
        run_native_bbb_search(
            keyword=keyword,
            location=location,
            max_profiles=max_profiles,
            headless=headless,
        )
    )
