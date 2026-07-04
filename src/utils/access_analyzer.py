from __future__ import annotations

import re


class BlockDetector:
    """
    Detects common anti-bot and access restriction pages.

    Returns:
        "" if no block detected,
        otherwise a human-readable reason.
    """

    @staticmethod
    def detect(html: str) -> str:
        html = (html or "").lower()

        checks = [
            ("Cloudflare Turnstile", "turnstile"),
            ("Cloudflare Challenge", "cf-challenge"),
            ("Cloudflare Protection", "checking your browser"),
            ("Cloudflare Protection", "attention required"),
            ("Human Verification", "verify you are human"),
            ("Human Verification", "verify you are a human"),
            ("CAPTCHA", "captcha"),
            ("Access Denied", "access denied"),
            ("Forbidden (403)", "403 forbidden"),
            ("Request Blocked", "request blocked"),
            ("Bot Protection", "bot protection"),
        ]

        for reason, token in checks:
            if token in html:
                return reason

        return ""

    @staticmethod
    def is_blocked(html: str) -> bool:
        return BlockDetector.detect(html) != ""
