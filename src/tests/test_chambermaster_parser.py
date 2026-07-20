from src.adapters.chambermaster import ChamberMasterParser


def test_parse_basic_contact_fields() -> None:
    html = """
    <html>
      <body>
        <h1 class="gz-pagetitle">Example Engineering LLC</h1>

        <div class="gz-card-phone">
          <span itemprop="telephone">(555) 123-4567</span>
        </div>

        <div class="gz-card-fax">
          <span itemprop="faxNumber">(555) 765-4321</span>
        </div>

        <div class="gz-card-website">
          <a href="https://example.com">Website</a>
        </div>

        <div class="gz-card-email">
          <a href="mailto:info@example.com?subject=Inquiry">Email</a>
        </div>

        <div itemprop="address">
          <span itemprop="streetAddress">123 Main Street</span>
          <span itemprop="addressLocality">Phoenix</span>
          <span itemprop="addressRegion">AZ</span>
          <span itemprop="postalCode">85001</span>
        </div>

        <div class="gz-card-description">
          Full-service civil engineering and transportation consulting firm.
        </div>

        <div class="gz-details-hours">
          <p class="gz-details-subtitle">Business Hours</p>
          <p>Monday-Friday, 8:00 AM-5:00 PM</p>
        </div>

        <div class="gz-details-driving">
          <p class="gz-details-subtitle">Driving Directions</p>
          <p>Located near Central Avenue and Main Street.</p>
        </div>

        <a href="https://www.facebook.com/exampleengineering">
          Facebook
        </a>
        <a href="https://www.linkedin.com/company/exampleengineering">
          LinkedIn
        </a>
        <a href="https://www.instagram.com/exampleengineering">
          Instagram
        </a>
        <a href="https://www.youtube.com/@exampleengineering">
          YouTube
        </a>
        <a href="https://x.com/exampleeng">
          X
        </a>
      </body>
    </html>
    """

    parser = ChamberMasterParser()
    profile = parser.parse_member_profile(
        html,
        category_names="Engineering",
        profile_url="https://directory.example/list/member/example",
    )

    assert profile.name == "Example Engineering LLC"
    assert profile.phone == "(555) 123-4567"
    assert profile.fax == "(555) 765-4321"
    assert profile.website == "https://example.com"
    assert profile.email == "info@example.com"

    assert profile.address == "123 Main Street"
    assert profile.city == "Phoenix"
    assert profile.state == "AZ"
    assert profile.postal_code == "85001"

    assert profile.description == (
        "Full-service civil engineering and transportation consulting firm."
    )

    assert profile.facebook == (
        "https://www.facebook.com/exampleengineering"
    )
    assert profile.linkedin == (
        "https://www.linkedin.com/company/exampleengineering"
    )
    assert profile.instagram == (
        "https://www.instagram.com/exampleengineering"
    )
    assert profile.youtube == (
        "https://www.youtube.com/@exampleengineering"
    )
    assert profile.twitter == "https://x.com/exampleeng"

    assert profile.category_names == "Engineering"
    assert profile.profile_url.endswith("/example")

    assert profile.hours == "Monday-Friday, 8:00 AM-5:00 PM"

    assert profile.driving_directions == (
        "Located near Central Avenue and Main Street."
    )


def test_parse_empty_member_profile() -> None:
    parser = ChamberMasterParser()
    profile = parser.parse_member_profile("")

    assert profile.name == ""
    assert profile.phone == ""
    assert profile.fax == ""
    assert profile.email == ""
    assert profile.website == ""
    assert profile.address == ""
    assert profile.city == ""
    assert profile.state == ""
    assert profile.postal_code == ""
    assert profile.description == ""
    assert profile.facebook == ""
    assert profile.linkedin == ""
    assert profile.instagram == ""
    assert profile.youtube == ""
    assert profile.twitter == ""
    assert profile.hours == ""
    assert profile.driving_directions == ""
