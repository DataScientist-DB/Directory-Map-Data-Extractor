# Universal Business Directory Intelligence Platform (UBDIP)

> Intelligent Business Directory Extraction, Website Enrichment, and Business Intelligence Scoring

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Apify](https://img.shields.io/badge/Apify-Actor-green.svg)
![License](https://img.shields.io/badge/License-MIT-blue.svg)

---

## Overview

Universal Business Directory Intelligence Platform (UBDIP) is an enterprise-grade Apify Actor for extracting, enriching, validating, and scoring business directory data.

Unlike traditional directory scrapers, UBDIP visits each company's own website, discovers additional contact information, extracts structured business metadata, and computes a Business Intelligence Score that helps prioritize the most complete and trustworthy business profiles.

UBDIP is designed for:

- B2B Lead Generation
- CRM Enrichment
- Market Intelligence
- Business Directories
- GIS & Spatial Intelligence
- Sales Prospecting
- Competitor Research
- Economic Development

---

## Key Features

### Universal Directory Crawling

- ChamberMaster
- Additional adapters (planned)

### Website Enrichment

Automatically visits company websites and extracts:

- Email addresses
- Phone numbers
- Contact pages
- About pages
- Social media profiles
- Company descriptions

### Schema.org Extraction

Extracts structured metadata including:

- Address
- Postal code
- Opening hours
- Organization schema

### Intelligent Contact Discovery

Automatically discovers:

- Contact pages
- About pages
- Additional website resources

### Business Intelligence Score (RC1.1)

Every business receives an intelligence score from **0–100** based on the richness and completeness of available information.

Scoring considers:

- Website
- Email
- Phone
- LinkedIn
- Facebook
- Instagram
- Twitter/X
- YouTube
- Schema.org metadata

Intelligence grades:

| Score | Grade |
|--------|-------|
| 90–100 | ★★★★★ Excellent |
| 70–89 | ★★★★ Good |
| 50–69 | ★★★ Fair |
| 30–49 | ★★ Poor |
| 0–29 | ★ Very Poor |

---

## Outputs

Supported formats:

- CSV
- XLSX

Each exported business contains:

- Company information
- Contact details
- Website enrichment
- Social media
- Business Intelligence Score
- Intelligence Grade

---

## Runtime Summary

After every execution UBDIP reports:

- Records exported
- Website enrichment statistics
- Social profile counts
- Business Intelligence summary
- Average Intelligence Score

---

## Architecture

```
Crawler
      │
      ▼
BusinessRecord
      │
      ▼
Website Enrichment
      │
      ▼
Schema Extraction
      │
      ▼
Contact Discovery
      │
      ▼
Business Intelligence Scoring
      │
      ▼
CSV / XLSX Export
```

---

## Project Status

Current release:

**Version:** RC1.1

Completed:

- Universal crawler
- ChamberMaster adapter
- Website enrichment
- Schema extraction
- Contact discovery
- Business Intelligence Layer
- Runtime statistics
- CSV/XLSX export
- Documentation
- Regression tests

---

## Roadmap

### RC1.2

- AI Business Summary
- Technology Detection
- Website Quality Score
- Contact Completeness Index
- Export Profiles
- JSON API

### Commercialization Sprint

- Apify Store optimization
- Demo video
- Pricing strategy
- Competitive positioning
- Professional screenshots

---

## License

MIT License
