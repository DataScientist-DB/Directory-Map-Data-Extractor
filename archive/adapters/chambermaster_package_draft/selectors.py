"""
ChamberMaster CSS selectors.

Centralizes all HTML selectors so changes in ChamberMaster layouts
can be handled in one place.
"""

TITLE = ".gz-pagetitle"

PHONE = ".gz-card-phone span[itemprop='telephone']"
FAX = ".gz-card-fax span[itemprop='faxNumber']"

WEBSITE = ".gz-card-website a[href]"
EMAIL = ".gz-card-email a[href^='mailto:']"

SOCIAL_LINKS = ".gz-card-social a[href]"

ADDRESS = ".gz-card-address"
STREET = ".gz-street-address"
CITY = ".gz-address-city"
STATE = "[itemprop='addressRegion']"
POSTAL_CODE = "[itemprop='postalCode']"

HOURS = ".gz-details-hours p:not(.gz-details-subtitle)"
DRIVING = ".gz-details-driving p:not(.gz-details-subtitle)"

DESCRIPTION_SELECTORS = (
    ".gz-details-description",
    ".gz-description",
    ".gz-member-description",
    ".gz-content",
    ".gz-card-description",
    "[itemprop='description']",
)

CATEGORY_TITLE_SELECTORS = (
    "h1",
    ".gz-pagetitle",
    ".mn-title",
    ".page-title",
    "title",
)
