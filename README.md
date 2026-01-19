Directory Listing Extractor
Clean, structured, Excel-ready directories from interactive maps and listing pages
This Actor extracts high-quality, analysis-ready datasets from directory and map pages such as NGO directories, agricultural maps, association member listings, partner registries, and store locators.
It is optimized for JavaScript-heavy websites where listing data is embedded directly in HTML or inline JavaScript objects (rather than rendered line-by-line in the DOM).
The output is designed to be immediately usable in Excel, Google Sheets, BI tools, or research workflows.
________________________________________
What this Actor does
For each organization, farm, or business listing found on a directory or map page, the Actor extracts structured information including:
Core fields
•	Entity / organization name
•	Location (city, region, country)
•	Address (when available)
•	Website
•	Profile or detail page URL
•	Public email address
•	Public phone number
Classification & enrichment
•	Categories (decoded into human-readable names)
•	Services (decoded into human-readable names)
•	Products (if available)
•	Semantic alignment of product labels to standardized categories
Optional descriptive fields
When available in the source data:
•	Size
•	Results / outcomes
•	Quotes / descriptions
•	Logos
Each listing is saved as one dataset item, normalized and ready for export.
________________________________________
Typical use cases
•	NGO and non-profit directories
•	Agricultural, food system, and sustainability maps
•	Association or member registries
•	Partner, supplier, or producer listings
•	Store locators and business directories
•	Market research, benchmarking, and data enrichment projects
Most users analyze results by entity name, category, or services, not by street-level geocoding.
________________________________________
Supported extraction modes
embedded_js (recommended)
Use this mode when listing data is embedded directly in the page HTML or JavaScript.
You configure:
•	embedded.anchorKey – a field that reliably exists in every listing object (used to detect listings)
•	embedded.keys – raw fields to extract from embedded objects
•	embedded.fieldMap – mapping from raw keys to clean output field names
This mode is:
•	Fast
•	Reliable
•	Stable on JS-heavy pages
•	Does not require clicking or pagination simulation
auto (future)
A future version may include automatic heuristics combining multiple extraction strategies.
________________________________________
Category & service decoding (important)
Many directories store categories and services as internal codes (for example: rpc5, rpc12, rss6).
These codes are not user-friendly on their own.
This Actor supports:
•	Static canonical taxonomies (built-in)
•	Automatic detection from embedded HTML or JavaScript (when available)
•	Manual overrides via input:
o	taxonomy.categoryMap
o	taxonomy.serviceMap
The output includes:
•	category_codes / service_codes (raw values)
•	category_names / service_names (human-readable, Excel-friendly)
This makes the dataset immediately usable for filtering, grouping, and reporting.
________________________________________
Product category normalization
Some directories expose product filters in the UI that are not stored as canonical categories.
This Actor:
•	Aligns product labels (e.g. Meat & poultry, Eggs, Vegetables) to standardized category codes
•	Preserves transparency between filters, products, and true entity categories
•	Avoids guessing or over-assignment
This is especially important for research-grade or policy-oriented datasets.
________________________________________
Quick start (default test)
The Actor includes a working default configuration:
•	Start URL:
https://regenerationcanada.org/en/map/
•	Mode: embedded_js
•	Max pages: 1
Simply click Run in the Apify Console to see results.
________________________________________
Input parameters (overview)
•	mode – Extraction strategy (default: embedded_js)
•	startUrls – One or more directory or map pages
•	maxListings – Safety cap on extracted listings
•	maxPages – Safety cap on visited pages
•	embedded.anchorKey – Field identifying listing objects
•	embedded.keys – Fields to extract from embedded objects
•	embedded.fieldMap – Rename raw fields to clean output fields
•	taxonomy.categoryMap – Optional manual category decoding
•	taxonomy.serviceMap – Optional manual service decoding
•	debug – Enable verbose logging for troubleshooting
________________________________________
Example output
Each dataset item is a normalized object, for example:
{
  "entity_name": "Southbrook Vineyards",
  "category_names": "Fruit; Value-added products",
  "service_names": "Farm tour (for general public)",
  "products": "Wine; Beef; Eggs",
  "email": "info@southbrook.com",
  "phone": "905-380-9095",
  "website": "https://www.southbrook.com",
  "location": "Niagara-on-the-Lake, Ontario",
  "profile_url": "https://regenerationcanada.org/en/southbrook-vineyard/",
  "source_url": "https://regenerationcanada.org/en/map/"
}
________________________________________
CSV / XLSX output (for clients & non-technical users)
Although data is processed internally as JSON, no JSON handling is required.
Delivered formats
•	CSV
•	XLSX (Excel)
Files are:
•	UTF-8 encoded
•	Excel-safe
•	Ready for Google Sheets or BI tools
Exporting from Apify Console
1.	Open the Actor run
2.	Go to the Dataset tab
3.	Click Export
4.	Choose CSV or XLSX
5.	Download
No additional configuration is required.

