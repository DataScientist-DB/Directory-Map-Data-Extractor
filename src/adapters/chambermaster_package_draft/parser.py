from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .models import RawMemberProfile
from . import selectors


class ChamberMasterParser:
    """
    Parses ChamberMaster member pages into RawMemberProfile.
    No Playwright.
    No BusinessRecord.
    """

    @staticmethod
    def clean(value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    def parse_member_profile(self, html: str) -> RawMemberProfile:

        soup = BeautifulSoup(html or "", "html.parser")

        profile = RawMemberProfile()

        #
        # Company Name
        #

        title = soup.select_one(selectors.TITLE)

        if title:
            profile.name = self.clean(
                title.get_text(" ", strip=True)
            )

        #
        # Phone
        #

        phone = soup.select_one(selectors.PHONE)

        if phone:
            profile.phone = self.clean(
                phone.get_text(" ", strip=True)
            )

        #
        # Fax
        #

        fax = soup.select_one(selectors.FAX)

        if fax:
            profile.fax = self.clean(
                fax.get_text(" ", strip=True)
            )

        return profile
