# Configuration Reference

## Overview

UBDI is configured through an INPUT.json file.

Every parameter is optional unless otherwise stated.

---

## Core Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| mode | string | auto | Crawl mode |
| maxListings | integer | 200 | Maximum number of businesses |
| maxPages | integer | 50 | Maximum pages to visit |
| debug | boolean | false | Enable debug logging |

---

## Enrichment

| Parameter | Type | Default |
|-----------|------|---------|
| enableProfileEnrichment | boolean | true |
| enableWebsiteEnrichment | boolean | false |
| websiteTimeoutMs | integer | 15000 |

---

## Output

| Parameter | Type | Default |
|-----------|------|---------|
| outputCsv | boolean | true |
| outputXlsx | boolean | false |
| outputBaseName | string | output |

---

## Taxonomy

...
