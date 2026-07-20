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
            <span itemprop="streetAddress">
                123 Main Street
            </span>

            <span itemprop="addressLocality">
                Phoenix
            </span>

            <span itemprop="addressRegion">
                AZ
            </span>

            <span itemprop="postalCode">
                85001
            </span>
        </div>

        <a href="https://www.facebook.com/exampleengineering">Facebook</a>
        <a href="https://www.linkedin.com/company/exampleengineering">LinkedIn</a>
        <a href="https://www.instagram.com/exampleengineering">Instagram</a>
        <a href="https://www.youtube.com/@exampleengineering">YouTube</a>
        <a href="https://x.com/exampleeng">X</a>

        assert profile.address == "123 Main Street"
        assert profile.city == "Phoenix"
        assert profile.state == "AZ"
        assert profile.postal_code == "85001"

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
    assert profile.category_names == "Engineering"
    assert profile.profile_url.endswith("/example")

    def test_parse_empty_member_profile() -> None:
        parser = ChamberMasterParser()
        profile = parser.parse_member_profile("")

        assert profile.name == ""
        assert profile.phone == ""
        assert profile.email == ""
        assert profile.website == ""
