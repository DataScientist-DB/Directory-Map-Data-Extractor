## Executive Summary

Universal Business Directory Intelligence (UBDI) is a modular Python framework for
extracting structured business information from online business directories.

The framework automatically detects supported directory architectures, delegates
extraction to the appropriate adapter, enriches business information using the
company's own website, validates extraction quality, and exports standardized
BusinessRecord objects to multiple output formats.

UBDI is designed around modularity, adapter independence, reusable enrichment,
and automated validation.

The framework is intended for:

- B2B lead generation
- Business intelligence
- Market research
- CRM enrichment
- Economic development
- Chamber of Commerce analysis
- GIS and spatial business intelligence

Every directory adapter must populate a BusinessRecord.

BusinessRecord is the canonical data model used throughout the platform.

All downstream components—including website enrichment, validation,
runtime reporting, exports, regression tests, and future APIs—operate
only on BusinessRecord instances.

Adapters should never communicate directly with downstream modules.

## Adapter Lifecycle

Every adapter follows the same lifecycle:

1. Directory detection
2. Directory-specific extraction
3. BusinessRecord creation
4. Website enrichment
5. Validation
6. Export
7. Runtime reporting

Directory Listing
        │
        ▼
Adapter
        │
        ▼
BusinessRecord
        │
        ▼
Schema.org
        │
        ▼
Homepage
        │
        ▼
Dynamic Contact Discovery
        │
        ▼
Contact Pages
        │
        ▼
Email Recovery
        │
        ▼
Phone Recovery
        │
        ▼
Social Profile Recovery
        │
        ▼
Website Cache
        │
        ▼
Export

## Validation Architecture

UBDI uses three complementary validation mechanisms.

### Smoke Test

Verifies that all core modules import correctly and can be instantiated.

### Regression Test

Verifies that extraction quality has not regressed by comparing current
results against expected minimum metrics.

### Runtime Summary

Summarizes extraction statistics, enrichment metrics, and output generation
after every execution.

## Future Development

### Platform

- REST API
- Web Dashboard
- Plugin architecture
- Automatic benchmarking
- Performance profiling

### Directory Adapters

- GrowthZone
- CivicPlus
- WildApricot
- Simpleview
- MemberClicks
- Custom React/Vue directories

## Architectural Decisions

### ADR-001

Adapters extract only directory-specific information.

### ADR-002

Website enrichment is platform-independent.

### ADR-003

BusinessRecord is the canonical business model.

### ADR-004

Validation is mandatory before release.

### ADR-005

Runtime statistics are generated for every execution.


