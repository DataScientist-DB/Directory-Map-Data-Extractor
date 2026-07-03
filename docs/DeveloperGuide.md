# Developer Guide

## Architecture

UBDIP is built as a modular pipeline.

```
Crawler
      ↓
BusinessRecord
      ↓
WebsiteEnricher
      ↓
SchemaExtractor
      ↓
ContactLinkDiscovery
      ↓
IntelligenceScore
      ↓
Export
```

---

## Main Components

### Crawler

Responsible for directory extraction.

### BusinessRecord

Central data model shared by all components.

### WebsiteEnricher

Performs website enrichment.

Responsibilities:

- Homepage analysis
- Contact page discovery
- About page discovery
- Email extraction
- Phone extraction
- Social extraction
- Schema.org extraction
- Intelligence scoring

### IntelligenceScore

Calculates Business Intelligence Score.

Current weights:

| Feature | Score |
|----------|------:|
| Website | 20 |
| Email | 20 |
| Phone | 20 |
| LinkedIn | 10 |
| Facebook | 10 |
| Instagram | 5 |
| Twitter/X | 5 |
| YouTube | 5 |
| Schema.org | 5 |

Maximum score:

100

---

## Export

Supported outputs:

- CSV
- XLSX

Export includes:

- Business information
- Contact information
- Website enrichment
- Business Intelligence Score
- Intelligence Grade

---

## Runtime Summary

Displays:

- Export statistics
- Website enrichment statistics
- Business Intelligence statistics

---

## Coding Guidelines

- Black formatting
- Type hints
- Small reusable classes
- Dependency injection
- Single responsibility
- Comprehensive logging

---

## Testing

Regression tests:

```
python tests/run_validation.py
```

Smoke tests:

```
python tests/run_smoke_tests.py
```

---

## Version

Current version:

RC1.1
