import pytest

from src.adapters.chambermaster import ChamberMasterAdapter


class MockPage:
    async def goto(self, *args, **kwargs):
        return None

    async def wait_for_timeout(self, *_):
        return None

    async def content(self):
        return """
        <html>
          <body>

            <h1 class="gz-pagetitle">
                Example Engineering LLC
            </h1>

            <div class="gz-card-phone">
                <span itemprop="telephone">
                    (555) 123-4567
                </span>
            </div>

            <div class="gz-card-email">
                <a href="mailto:info@example.com">
                    Email
                </a>
            </div>

            <div class="gz-card-website">
                <a href="https://example.com">
                    Website
                </a>
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

            <div class="gz-card-description">
                Transportation engineering specialists.
            </div>

          </body>
        </html>
        """


@pytest.mark.asyncio
async def test_extract_member_pipeline():

    adapter = ChamberMasterAdapter()

    adapter.source_url = "https://directory.example"

    adapter.architecture = "chambermaster"

    page = MockPage()

    result = await adapter.extract_member(
        page,
        {
            "url": "https://directory.example/member/example",
            "category_names": "Engineering",
        },
    )

    assert result["entity_name"] == "Example Engineering LLC"

    assert result["phone"] == "(555) 123-4567"

    assert result["email"] == "info@example.com"

    assert result["website"] == "https://example.com"

    assert result["address"] == "123 Main Street"

    assert result["city"] == "Phoenix"

    assert result["state"] == "AZ"

    assert result["postal_code"] == "85001"

    assert (
        result["description"]
        == "Transportation engineering specialists."
    )

    assert result["category_names"] == "Engineering"

    assert result["architecture"] == "chambermaster"

    assert result["source_url"] == "https://directory.example"
