from src.enrichment.email_extractor import EmailExtractor
from src.enrichment.phone_extractor import PhoneExtractor
from src.enrichment.social_extractor import SocialExtractor
from src.enrichment.schema_extractor import SchemaExtractor
from src.enrichment.website_quality import WebsiteQuality


def test_website_enrichment_components():
    html = """
    <html>
      <head>
        <title>Acme Engineering</title>
        <meta name="description" content="Traffic engineering and transport planning company.">
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "LocalBusiness",
          "name": "Acme Engineering",
          "telephone": "+1 949 555 1212",
          "email": "contact@acme.com",
          "address": {
            "@type": "PostalAddress",
            "streetAddress": "100 Main Street",
            "addressLocality": "Irvine",
            "addressRegion": "CA",
            "postalCode": "92618"
          }
        }
        </script>
      </head>
      <body>
        <a href="mailto:sales@acme.com">Sales</a>
        <a href="https://www.linkedin.com/company/acme-engineering">LinkedIn</a>
        <a href="https://www.facebook.com/acmeengineering">Facebook</a>
        Call us: +1 949 555 1212
      </body>
    </html>
    """

    emails = EmailExtractor().extract(html)
    phone = PhoneExtractor().extract(html)
    social = SocialExtractor().extract(html)
    schema = SchemaExtractor().extract(html)
    quality = WebsiteQuality().analyze(html=html, url="https://acme.com")

    assert emails
    assert emails[0].email in {"sales@acme.com", "contact@acme.com"}

    assert phone
    platforms = {item.platform: item.url for item in social}

    assert platforms["linkedin"]
    assert platforms["facebook"]

    assert schema.get("email") == "contact@acme.com"
    assert schema.get("phone") == "+1 949 555 1212"
    assert schema.get("city") == "Irvine"

    assert quality
