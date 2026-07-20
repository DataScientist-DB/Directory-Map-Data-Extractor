# Changelog

All notable changes to the **Universal Business Directory Intelligence
Platform (UBDIP)** are documented in this file.

The project follows a release-candidate development model where each
milestone introduces stable architectural improvements toward the v2.0
platform.

------------------------------------------------------------------------

# v1.0.0-rc1.5 --- Website Intelligence Foundation

## Added

### Architecture

-   Introduced layered architecture:
    -   Discovery
    -   Access
    -   Enrichment
    -   Intelligence
    -   Export
-   Added `AdapterCapabilities`
-   Added `BaseExtractor`
-   Added `BaseEnricher`

### Models

-   EmailRecord
-   PhoneRecord
-   SocialRecord
-   SchemaRecord
-   WebsiteRecord

### Website Intelligence

-   EmailExtractor v2
-   PhoneExtractor v2
-   SocialExtractor v2
-   Email classification
-   Phone classification
-   Social classification
-   Quality scoring
-   Website quality analysis

### Engineering

-   pytest configuration
-   Unit tests
-   Record-based enrichment architecture

## Changed

-   Refactored WebsiteEnricher for model-based enrichment
-   Separated Intelligence layer from Enrichment layer
-   Improved project package structure

## Fixed

-   Export compatibility after record migration
-   Website enrichment integration
-   Runtime stability

------------------------------------------------------------------------

# v1.0.0-rc1.1 --- Business Intelligence Scoring

## Added

-   Business Intelligence Score
-   Intelligence Grade
-   Runtime intelligence summary
-   Intelligence export to CSV
-   Intelligence export to XLSX

## Improved

-   WebsiteEnricher integration
-   Runtime reporting
-   Export pipeline

## Fixed

-   Export column synchronization
-   Runtime statistics

------------------------------------------------------------------------

# v1.0.0-rc1 --- Universal Discovery Engine

## Added

### Discovery

-   Universal crawler
-   ChamberMaster adapter
-   BBB adapter
-   Adapter router

### Access

-   BrowserFactory
-   ProxyManager
-   Access diagnostics
-   AccessReport

### Enrichment

-   Website enrichment
-   Contact page discovery
-   Schema.org extraction
-   Email extraction
-   Phone extraction
-   Social extraction
-   Website cache

### Export

-   CSV export
-   XLSX export
-   Runtime summary

### Documentation

-   Product Charter
-   Architecture documentation
-   Configuration guide
-   Developer guide
-   Examples
-   CONTRIBUTING
-   LICENSE
-   CODE_OF_CONDUCT

------------------------------------------------------------------------

# Upcoming Releases

## RC1.6

-   Business Intelligence Engine
-   WebsiteScore
-   BusinessScore
-   TrustScore
-   DirectoryScore

## RC1.7

-   AI Intelligence
-   AI Business Profiles
-   AI Classification

## RC1.8

-   Universal Directory Platform
-   Additional adapters
-   REST API
-   JSON export
-   CRM connectors

## RC2.0

-   Enterprise Intelligence Platform
-   Plugin ecosystem
-   Dashboard
-   Advanced analytics
