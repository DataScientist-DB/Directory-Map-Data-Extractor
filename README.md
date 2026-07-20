# Universal Business Directory Intelligence Platform (UBDIP)

> **Discover. Enrich. Classify. Score. Export.**

UBDIP is a modular business directory intelligence framework designed to
discover business listings, enrich them from company websites, evaluate
their quality, and export business-ready datasets. Unlike a traditional
scraper, UBDIP separates **discovery**, **access**, **enrichment**,
**intelligence**, and **export** into independent layers.

------------------------------------------------------------------------

# Current Release

**Version:** `v1.0.0-rc1.5`

## RC1.5 Highlights

-   Universal adapter framework
-   ChamberMaster adapter
-   BBB adapter with access diagnostics
-   Website enrichment pipeline
-   EmailRecord, PhoneRecord, SocialRecord and WebsiteRecord models
-   EmailExtractor v2
-   PhoneExtractor v2
-   SocialExtractor v2
-   Website quality analysis
-   Business Intelligence Score v1
-   CSV/XLSX export
-   pytest integration with unit tests

------------------------------------------------------------------------

# Architecture

    Discovery
        │
        ▼
    Access
        │
        ▼
    Enrichment
        │
        ▼
    Intelligence
        │
        ▼
    Export

## Discovery Layer

-   Universal adapter architecture
-   Directory routing
-   Pagination
-   Search requests

## Access Layer

-   BrowserFactory
-   ProxyManager
-   Access diagnostics
-   Access reports

## Enrichment Layer

Extracts information directly from company websites:

-   Email
-   Phone
-   Social profiles
-   Schema.org
-   Contact/About pages
-   Website quality

## Intelligence Layer

Computes business intelligence from enriched records.

Current: - IntelligenceScore v1

Planned: - WebsiteScore - BusinessScore - TrustScore - DirectoryScore

## Export Layer

Current: - CSV - XLSX

Planned: - JSON - SQLite - REST API - CRM connectors - HubSpot -
Salesforce

------------------------------------------------------------------------

# Supported Directory Types

-   Business directories
-   Chamber directories
-   Membership directories
-   Association directories
-   Government registries
-   Protected directories

------------------------------------------------------------------------

# Access Diagnostics

UBDIP detects blocked platforms and reports:

-   HTTP status
-   Protection mechanism
-   Pages visited
-   Profiles discovered
-   Recommended access strategy

This allows protected platforms (such as BBB) to fail gracefully with
actionable diagnostics instead of silent failures.

------------------------------------------------------------------------

# Testing

Run the crawler:

``` bash
python -m src.main
```

Run tests:

``` bash
pytest
```

------------------------------------------------------------------------

# Project Status

  Component                          Status
  --------------------------------- --------
  Universal Adapter Framework          ✅
  Discovery Engine                     ✅
  Access Diagnostics                   ✅
  Website Intelligence Foundation      ✅
  Business Intelligence v1             ✅
  Unit Tests                           ✅
  Business Intelligence Engine         🚧

------------------------------------------------------------------------

# Roadmap

-   ✅ RC1.0 Universal Discovery Engine
-   ✅ RC1.1 Business Intelligence Scoring
-   ✅ RC1.5 Website Intelligence Foundation
-   ⏳ RC1.6 Business Intelligence Engine
-   ⏳ RC1.7 AI Intelligence & Classification
-   ⏳ RC1.8 Universal Directory Platform
-   ⏳ RC2.0 Enterprise Intelligence Platform

------------------------------------------------------------------------

# Repository Structure

    src/
     ├── adapters/
     ├── access/
     ├── browser/
     ├── enrichment/
     ├── intelligence/
     ├── models/
     ├── network/
     ├── presets/
     ├── tests/
     └── main.py

------------------------------------------------------------------------

# Contributing

Contributions are welcome. New directory adapters, enrichment modules,
tests, and documentation improvements are encouraged.

------------------------------------------------------------------------

# License

MIT License
