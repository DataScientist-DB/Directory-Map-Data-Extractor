from src.enrichment.email_extractor import EmailExtractor


def test_email_extractor_v2():
    html = """
    <html>
      <body>
        <a href="mailto:info@acme.com">Email us</a>
        sales@acme.com
        ceo@acme.com
        admin@gmail.com
      </body>
    </html>
    """

    records = EmailExtractor().extract(html)

    assert len(records) == 4

    emails = [r.email for r in records]

    assert "info@acme.com" in emails
    assert "sales@acme.com" in emails
    assert "ceo@acme.com" in emails
    assert "admin@gmail.com" in emails

    by_email = {r.email: r for r in records}

    assert by_email["ceo@acme.com"].classification == "executive"
    assert by_email["sales@acme.com"].classification == "sales"
    assert by_email["info@acme.com"].classification == "general"
    assert by_email["admin@gmail.com"].classification == "free_provider"

    assert by_email["ceo@acme.com"].quality_score >= by_email["info@acme.com"].quality_score
    assert by_email["admin@gmail.com"].quality_score < by_email["info@acme.com"].quality_score
