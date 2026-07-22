from __future__ import annotations

from src.models.access_report import AccessReport


class AccessAnalyzer:
    """
    Universal access diagnostics for directory adapters.
    """

    @staticmethod
    def analyze(
        html: str,
        http_status: int = 200,
    ) -> AccessReport:
        report = AccessReport(http_status=http_status)

        text = (html or "").lower()

        checks = [
            ("Cloudflare Turnstile", "turnstile"),
            ("Cloudflare Challenge", "cf-challenge"),
            ("Cloudflare Protection", "checking your browser"),
            ("Cloudflare Protection", "attention required"),
            ("Human Verification", "verify you are human"),
            ("Human Verification", "verify you are a human"),
            ("CAPTCHA", "captcha"),
            ("Access Denied", "access denied"),
            ("Forbidden", "403 forbidden"),
            ("Too Many Requests", "429"),
            ("Request Blocked", "request blocked"),
        ]

        for reason, token in checks:
            if token in text:
                report.status = "blocked"
                report.blocked_reason = reason
                break

        if http_status == 403:
            report.status = "blocked"
            if not report.blocked_reason:
                report.blocked_reason = "HTTP 403"

        elif http_status == 429:
            report.status = "blocked"
            if not report.blocked_reason:
                report.blocked_reason = "HTTP 429"

        if report.blocked():
            recommendations = {
                "Cloudflare Turnstile": "Use Apify Residential Proxy.",
                "Cloudflare Challenge": "Retry using Residential Proxy.",
                "CAPTCHA": "Manual session or CAPTCHA solving may be required.",
                "HTTP 403": "Verify access permissions or enable Residential Proxy.",
                "HTTP 429": "Reduce crawl rate and retry later.",
            }

            report.recommendation = recommendations.get(
                report.blocked_reason,
                "Review access configuration.",
            )

        return report
