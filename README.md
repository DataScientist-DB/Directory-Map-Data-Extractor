# Directory Listing Extractor

## Extract Structured Directory Listings from Interactive Maps and Business Directories

Transform interactive maps, business directories, association registries, NGO databases, supplier networks, member directories, and producer listings into clean, structured, Excel-ready datasets.

The Directory Listing Extractor is optimized for modern JavaScript-powered websites where listing information is embedded in HTML, JSON, or JavaScript objects rather than rendered directly in the page content.

The Actor automatically extracts business details, websites, emails, phone numbers, categories, services, products, and other metadata and exports them into structured datasets ready for analysis.

---

# Screenshots

## Structured Directory Listings

![Structured Directory Listings](images/screenshot-1-structured-listings.png)

Extract clean organization records with locations, websites, categories, and services.

---

## Category & Service Classification

![Category & Service Classification](images/screenshot-2-category-service-classification.png)

Decode internal category and service codes into human-readable business intelligence fields.

---

## Excel Export

![Excel Export](images/screenshot-3-excel-export.png)

Export ready-to-use CSV and Excel files for Google Sheets, CRM systems, and BI tools.

---

## Actor Configuration

![Actor Configuration](images/screenshot-4-actor-configuration.png)

Configure target directory URLs, output format, and extraction limits.


# What This Actor Extracts

For each organization, business, farm, supplier, member, or directory listing discovered, the Actor extracts structured information including:

## Core Fields

- Entity name
- Location
- Address
- Website
- Profile URL
- Public email address
- Public phone number

## Classification & Enrichment

- Category codes
- Service codes
- Category names
- Service names
- Products
- Classification mappings

## Additional Metadata

When available:

- Size
- Results
- Descriptions
- Quotes
- Logos

Each listing is normalized into a clean dataset item.

---
## Recommended Output

For non-technical users, use the generated files in Key-Value Store:

- `output.xlsx`
- `output.csv`

These files include cleaned, Excel-ready fields with decoded category and service names.

The Apify Dataset is also available for developers and API users, but it may include raw internal fields such as category and service codes.

# Example Output

```json
{
  "entity_name": "Southbrook Vineyards",
  "location": "Niagara-on-the-Lake, Ontario",
  "website": "https://www.southbrook.com",
  "email": "info@southbrook.com",
  "phone": "905-380-9095",
  "category_names_str": "Fruit; Value-added products",
  "service_names_str": "Farm tour (for general public)",
  "products": "Wine; Beef; Eggs",
  "profile_url": "https://regenerationcanada.org/en/southbrook-vineyard/",
  "source_url": "https://regenerationcanada.org/en/map/"
}
```

---

# Typical Use Cases

### Business Directories

- Company directories
- Local business listings
- Store locators
- Supplier directories

### Associations

- Member registries
- Professional organizations
- Industry directories

### NGOs & Nonprofits

- NGO databases
- Community networks
- Nonprofit ecosystems

### Agriculture & Sustainability

- Farm directories
- Producer networks
- Sustainability maps
- Food system ecosystems

### Research & Intelligence

- Market research
- Competitor analysis
- Industry mapping
- Data enrichment

---

# Supported Extraction Mode

## embedded_js (Recommended)

Use this mode when listing information is embedded inside:

- JavaScript variables
- JSON objects
- Inline scripts
- Structured page data

Advantages:

- Fast
- Reliable
- Stable
- Works on modern websites
- No browser interaction required

---

# Category & Service Classification

Many directory websites store classifications using internal codes.

Examples:

```text
rpc1
rpc5
rpc12

rss6
rss10
```

The Actor automatically converts them into human-readable values.

Examples:

```text
rpc1  → Beef
rpc5  → Vegetables
rpc12 → Value-added products

rss6  → Farm tour (for other farmers)
rss10 → Wwoofing
```

Output fields include:

```text
category_codes
service_codes

category_names
service_names

category_names_str
service_names_str
```

This makes the output immediately usable in Excel, Power BI, Tableau, and CRM systems.

---

# Product Classification

The Actor also performs semantic alignment between products and categories.

Examples:

| Product    | Category             |
|------------|----------------------|
| Eggs       | Poultry              |
| Honey      | Honey & bee products |
| Vegetables | Vegetables           |
| Dairy      | Dairy                |
| Wine       | Value-added products |

This improves reporting and downstream analytics.

---

# Export Formats

The Actor automatically generates:

## CSV Export

```text
output.csv
```

## Excel Export

```text
output.xlsx
```

Files are:

- UTF-8 encoded
- Excel compatible
- Google Sheets compatible
- BI-tool ready

---

# Sample Results

The Actor successfully extracts records such as:

| Entity              | Category                  | Services                       |
|---------------------|---------------------------|--------------------------------|
| Vallée Des Prairies | Pork; Vegetables          | Farm tours; Volunteer program  |
| Benjamin Bridge     | Beef; Dairy               | Direct sales                   |
| Rustik Bison        | Beef                      | Farm tours; Events             |
| South Glanton Farms | Beef; Pork; Lamb          | Farm tours; Internship program |
| Juniper Farm        | Beef; Poultry; Vegetables | Pick-your-own                  |

---

# Quick Start

Default test configuration:

```json
{
  "mode": "embedded_js",
  "startUrls": [
    {
      "url": "https://regenerationcanada.org/en/map/"
    }
  ],
  "maxListings": 500,
  "outputCsv": true,
  "outputXlsx": true
}
```

Click **Run** and review the generated dataset.

---

# Input Parameters

| Parameter            | Description                 |
|----------------------|-----------------------------|
| mode                 | Extraction strategy         |
| startUrls            | One or more directory URLs  |
| maxListings          | Maximum number of listings  |
| maxPages             | Maximum pages to process    |
| embedded.anchorKey   | Listing detection field     |
| embedded.keys        | Fields to extract           |
| embedded.fieldMap    | Field mapping configuration |
| taxonomy.categoryMap | Custom category mappings    |
| taxonomy.serviceMap  | Custom service mappings     |
| outputCsv            | Generate CSV export         |
| outputXlsx           | Generate Excel export       |
| debug                | Enable verbose logging      |

---

# Output Columns

## Default Export

```text
entity_name
location
address
phone
email
website
profile_url
category_names_str
service_names_str
products
source_url
```

## Additional Fields

```text
category_codes
service_codes
category_names
service_names
logo
logo_medium
lat
lng
quote
size
results
```

---

# Ideal For

✅ Business Intelligence

✅ Lead Generation

✅ Market Research

✅ Supplier Discovery

✅ Association Directories

✅ NGO Mapping

✅ Agricultural Networks

✅ CRM Enrichment

✅ Competitive Analysis

✅ Ecosystem Intelligence

---

# Exporting Results

1. Run the Actor
2. Open the Dataset tab
3. Click Export
4. Choose CSV or XLSX
5. Download the file

No additional processing is required.

---

# Why Use This Actor?

Unlike generic web scrapers, this Actor is specifically designed for structured directory and map websites where data is hidden inside JavaScript objects and embedded content.

Key benefits:

- Structured extraction
- Category decoding
- Service decoding
- Excel-ready output
- Contact information extraction
- Product classification
- Fast execution
- Research-grade datasets

Perfect for analysts, researchers, consultants, lead-generation teams, NGOs, and market intelligence professionals.