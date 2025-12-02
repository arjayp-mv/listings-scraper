# Product Requirements Document
## Channel SKU Metrics Feature (Product Details Scraper)

**Version:** 1.0  
**Date:** December 2024  
**Status:** Draft  
**Parent System:** Amazon Reviews Scraper Tool

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Feature Overview](#2-feature-overview)
3. [User Stories](#3-user-stories)
4. [Functional Requirements](#4-functional-requirements)
5. [Technical Architecture](#5-technical-architecture)
6. [Database Schema](#6-database-schema)
7. [API Endpoints](#7-api-endpoints)
8. [UI/UX Specifications](#8-uiux-specifications)
9. [Future Considerations](#9-future-considerations)
10. [Appendix](#10-appendix)

---

## 1. Executive Summary

### 1.1 Purpose

This document outlines requirements for the **Channel SKU Metrics** feature, an addition to the existing Amazon Reviews Scraper tool. This feature enables batch scraping of product ratings and review counts for the company's own Amazon listings.

### 1.2 Problem Statement

The team needs to monitor product performance metrics (ratings and review counts) across hundreds to thousands of Channel SKUs. Currently, this data must be checked manually on Amazon, making it difficult to:
- Track listing health at scale
- Identify products with declining ratings
- Monitor review accumulation over time

### 1.3 Proposed Solution

A batch scraping feature that:
- Accepts bulk input of Channel SKUs with their ASINs
- Scrapes current rating and review count from Amazon
- Displays results in an easy-to-analyze table
- Exports to Excel/CSV for further analysis
- Tracks changes over time

### 1.4 Key Benefits

- Monitor hundreds of listings in minutes instead of hours
- Identify problem listings (low ratings) quickly
- Track metrics history over time
- Export data for reporting and analysis
- Foundation for scheduled health checks

---

## 2. Feature Overview

### 2.1 Scope

#### In Scope (This Phase)

- Batch product details scraping via Apify
- Input via textarea or CSV file upload
- Multi-marketplace support
- Results table with sorting/filtering
- Excel/CSV export
- Job history and re-run capability
- Channel SKU change history (ASIN updates)
- Integration with existing SKU table

#### Out of Scope (Future Phases)

- Scheduled/recurring scrapes
- Historical trend charts
- Alerts for rating drops
- Competitor listings research
- Additional product data fields (price, inventory, etc.)

### 2.2 Apify Actor

**Actor:** `axesso_data~amazon-product-details-scraper`

**Input Format:**
```json
{
  "urls": [
    "https://www.amazon.com/dp/B0106TGBCA",
    "https://www.amazon.com/dp/B0106TGBY8"
  ]
}
```

**Key Output Fields Used:**
| Field | Type | Description |
|-------|------|-------------|
| productRating | String | "4.5 out of 5 stars" (parsed to numeric) |
| countReview | Integer | Number of reviews |
| title | String | Product title (for verification) |
| asin | String | Confirmed ASIN from Amazon |

### 2.3 Updated Navigation Structure

```
Dashboard | New Scrape | Jobs | Channel SKU Metrics | SKUs | Settings
                              └── New Scan
                              └── Scan History  
                              └── All Listings
```

---

## 3. User Stories

### 3.1 Core Workflows

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| US-01 | As a user, I want to submit a batch of Channel SKUs for metrics scraping | • Can enter data via textarea (tab or comma separated)<br>• Can upload CSV file<br>• Supports 100s of entries per job<br>• Auto-splits large batches into multiple jobs |
| US-02 | As a user, I want to select which marketplace to scrape | • Dropdown to select marketplace<br>• Default: Amazon.com<br>• URLs constructed automatically from ASIN + marketplace |
| US-03 | As a user, I want to see results in a clear table format | • Columns: SKU, Channel SKU, ASIN, Rating, Reviews<br>• Rating shown as numeric (4.5 not "4.5 out of 5 stars")<br>• Sortable by any column<br>• Filterable by SKU, rating range |
| US-04 | As a user, I want to export results | • Export to Excel (.xlsx)<br>• Export to CSV<br>• Include all columns plus product title |
| US-05 | As a user, I want to see all my listings with latest metrics | • Master view of all Channel SKUs ever scraped<br>• Shows most recent rating/review count<br>• Shows last scraped date<br>• Filterable and sortable |
| US-06 | As a user, I want to track when ASINs change | • System detects if ASIN changed for Channel SKU + Marketplace<br>• Keeps history of ASIN changes<br>• Shows change indicator in UI |
| US-07 | As a user, I want to retry failed ASINs | • Failed ASINs shown with error message<br>• Option to retry just failed ones<br>• Partial success still saves successful results |

---

## 4. Functional Requirements

### 4.1 New Scan Page

Primary interface for initiating product metrics scraping.

#### Input Methods

**Option 1: Textarea Input**
- Accepts tab-separated or comma-separated values
- Auto-detects delimiter
- Format: `SKU, Channel SKU, ASIN`
- One entry per line

**Option 2: CSV File Upload**
- Drag-and-drop or file browser
- Accepts .csv and .txt files
- Same format as textarea
- Shows preview of first 5 rows before submission

#### Input Fields

| Field | Type | Default | Required |
|-------|------|---------|----------|
| Job Name | Text input | - | Yes |
| Marketplace | Dropdown | Amazon.com (com) | Yes |
| Skip Header Row | Checkbox | Unchecked | No |
| Input Data | Textarea OR File Upload | - | Yes |

#### Marketplace Options

| Domain Code | Marketplace | URL Pattern |
|-------------|-------------|-------------|
| com | Amazon.com | amazon.com/dp/{ASIN} |
| ca | Amazon.ca | amazon.ca/dp/{ASIN} |
| co.uk | Amazon.co.uk | amazon.co.uk/dp/{ASIN} |
| de | Amazon.de | amazon.de/dp/{ASIN} |
| fr | Amazon.fr | amazon.fr/dp/{ASIN} |
| it | Amazon.it | amazon.it/dp/{ASIN} |
| es | Amazon.es | amazon.es/dp/{ASIN} |
| co.jp | Amazon.co.jp | amazon.co.jp/dp/{ASIN} |
| com.au | Amazon.com.au | amazon.com.au/dp/{ASIN} |
| com.mx | Amazon.com.mx | amazon.com.mx/dp/{ASIN} |

#### Input Validation

- ASIN format validation (10 alphanumeric characters)
- Duplicate detection within same submission
- Required fields check (SKU, Channel SKU, ASIN all required)
- Show validation errors before submission

#### Batch Handling

- If input exceeds batch limit (configurable, default 200), auto-split into multiple jobs
- Show user: "Your 450 listings will be split into 3 jobs"
- Jobs run sequentially in queue
- Results can be viewed per-job or combined

### 4.2 Scan History Page

View all product metrics scraping jobs.

#### Job List Columns

- Job Name
- Marketplace
- Total Listings
- Completed / Failed
- Status
- Created Date
- Actions (View, Re-run, Delete)

#### Job Statuses

| Status | Color | Description |
|--------|-------|-------------|
| Queued | Gray | Waiting to process |
| Running | Blue (animated) | Currently scraping |
| Completed | Green | All listings scraped successfully |
| Partial | Yellow | Some listings failed |
| Failed | Red | Job failed completely |
| Cancelled | Gray | Cancelled by user |

### 4.3 Job Results Page

View results from a completed scan job.

#### Results Table Columns

| Column | Sortable | Filterable | Notes |
|--------|----------|------------|-------|
| SKU | Yes | Yes (dropdown) | Link to SKU detail page |
| Channel SKU | Yes | Yes (text search) | - |
| ASIN | Yes | Yes (text search) | Link to Amazon page |
| Rating | Yes | Yes (range slider) | Numeric, e.g., 4.5 |
| Reviews | Yes | Yes (range) | Integer count |
| Status | Yes | Yes (dropdown) | Success/Failed |

#### Features

- **Search:** Global search across all text columns
- **Sort:** Click column header to sort (asc/desc toggle)
- **Filter:** 
  - SKU dropdown (multi-select)
  - Rating range slider (e.g., 1.0 - 5.0)
  - Review count range
  - Status filter
- **Pagination:** 50 results per page
- **Summary Stats:**
  - Total listings scraped
  - Average rating
  - Total reviews
  - Failed count

#### Export Options

- **Export Excel:** All results with all columns including Product Title
- **Export CSV:** Same data in CSV format
- **Copy Table:** Copy visible rows to clipboard

#### Failed Listings Section

- Separate tab or collapsible section for failed ASINs
- Shows: SKU, Channel SKU, ASIN, Error Message
- "Retry Failed" button to requeue just failed ones

### 4.4 All Listings Page

Master view of all Channel SKUs with their latest metrics.

#### Table Columns

| Column | Description |
|--------|-------------|
| SKU | Parent SKU |
| Channel SKU | Unique channel identifier |
| ASIN | Current ASIN |
| Marketplace | Amazon domain |
| Rating | Most recent rating |
| Reviews | Most recent review count |
| Last Scraped | Date of last successful scrape |
| History | Icon if ASIN has changed |

#### Features

- **Filtering:** By SKU, Marketplace, Rating range
- **Sorting:** Any column
- **Search:** Text search on SKU/Channel SKU/ASIN
- **Export:** Full listing export to Excel
- **Bulk Actions:** Select multiple for re-scan

#### ASIN Change Indicator

- Icon/badge shown if ASIN was updated
- Hover to see: "ASIN changed from B00XXX to B00YYY on Dec 1, 2024"
- Click to view full ASIN history for that Channel SKU

---

## 5. Technical Architecture

### 5.1 Integration with Existing System

This feature integrates with the existing Amazon Reviews Scraper:

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│  Dashboard │ Reviews │ Channel SKU Metrics │ SKUs │ Settings    │
└─────────────────────────────┬───────────────────────────────────┘
                              │ REST API
┌─────────────────────────────┴───────────────────────────────────┐
│                         BACKEND                                  │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │ Reviews Scraper │    │ Product Scraper │  ← NEW              │
│  │    Service      │    │    Service      │                     │
│  └────────┬────────┘    └────────┬────────┘                     │
│           │                      │                               │
│           └──────────┬───────────┘                               │
│                      │                                           │
│              ┌───────┴───────┐                                   │
│              │  Job Queue    │                                   │
│              │  (shared)     │                                   │
│              └───────────────┘                                   │
└──────────┬──────────────────────────────────────────┬───────────┘
           │                                          │
           ▼                                          ▼
    ┌──────────────┐                         ┌────────────────┐
    │   MySQL DB   │                         │   Apify API    │
    │  (extended)  │                         │ Product Actor  │
    └──────────────┘                         └────────────────┘
```

### 5.2 URL Construction

The Apify actor requires full URLs. System constructs URLs from ASIN + Marketplace:

```python
def construct_amazon_url(asin: str, marketplace: str) -> str:
    domain_map = {
        "com": "amazon.com",
        "ca": "amazon.ca",
        "co.uk": "amazon.co.uk",
        "de": "amazon.de",
        # ... etc
    }
    domain = domain_map.get(marketplace, "amazon.com")
    return f"https://www.{domain}/dp/{asin}"
```

### 5.3 Rating Parsing

Convert rating string to numeric:

```python
def parse_rating(rating_str: str) -> float:
    # Input: "4.5 out of 5 stars"
    # Output: 4.5
    if not rating_str:
        return None
    match = re.search(r'(\d+\.?\d*)\s*out of', rating_str)
    return float(match.group(1)) if match else None
```

### 5.4 Batch Processing

```python
BATCH_SIZE = 200  # Configurable in settings

def split_into_batches(listings: list) -> list[list]:
    """Split large input into manageable batches"""
    return [listings[i:i + BATCH_SIZE] 
            for i in range(0, len(listings), BATCH_SIZE)]
```

### 5.5 Job Queue Integration

Uses same job queue as reviews scraper:
- Job type field distinguishes: `review_scrape` vs `product_scrape`
- Same worker processes both types
- Same delay settings apply

---

## 6. Database Schema

### 6.1 New Tables

#### channel_skus

Stores all Channel SKUs with their current ASIN mapping.

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT PK AUTO | Primary key |
| sku_id | BIGINT FK | Reference to skus table |
| channel_sku | VARCHAR(100) | Channel SKU identifier |
| marketplace | VARCHAR(10) | Amazon domain code |
| current_asin | VARCHAR(15) | Current ASIN |
| product_title | VARCHAR(500) | Product title from Amazon |
| latest_rating | DECIMAL(2,1) | Most recent rating (e.g., 4.5) |
| latest_review_count | INT | Most recent review count |
| last_scraped_at | TIMESTAMP | Last successful scrape |
| created_at | TIMESTAMP | First time added |
| updated_at | TIMESTAMP | Last update |

**Unique Constraint:** (channel_sku, marketplace)

#### channel_sku_asin_history

Tracks ASIN changes for Channel SKUs.

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT PK AUTO | Primary key |
| channel_sku_id | BIGINT FK | Reference to channel_skus |
| asin | VARCHAR(15) | The ASIN at this time |
| changed_at | TIMESTAMP | When this ASIN was set |
| changed_by_job_id | BIGINT FK | Job that detected change |

#### product_scan_jobs

Similar to scrape_jobs but for product metrics.

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT PK AUTO | Primary key |
| job_name | VARCHAR(255) | User-provided name |
| status | ENUM | queued, running, completed, partial, failed, cancelled |
| marketplace | VARCHAR(10) | Target marketplace |
| total_listings | INT | Number of listings to scrape |
| completed_listings | INT | Successfully scraped |
| failed_listings | INT | Failed to scrape |
| apify_delay_seconds | INT DEFAULT 10 | Delay between calls |
| error_message | TEXT | Error if failed |
| created_at | TIMESTAMP | Job creation |
| started_at | TIMESTAMP | Processing start |
| completed_at | TIMESTAMP | Completion time |

#### product_scan_items

Individual listings within a scan job.

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT PK AUTO | Primary key |
| job_id | BIGINT FK | Reference to product_scan_jobs |
| channel_sku_id | BIGINT FK | Reference to channel_skus |
| input_asin | VARCHAR(15) | ASIN provided in input |
| status | ENUM | pending, running, completed, failed |
| scraped_rating | DECIMAL(2,1) | Rating from scrape |
| scraped_review_count | INT | Review count from scrape |
| scraped_title | VARCHAR(500) | Title from scrape |
| scraped_asin | VARCHAR(15) | ASIN returned by Amazon |
| apify_run_id | VARCHAR(50) | Apify run tracking |
| error_message | TEXT | Error if failed |
| started_at | TIMESTAMP | Processing start |
| completed_at | TIMESTAMP | Processing end |

### 6.2 Updated Tables

#### skus (existing table - no changes needed)

Channel SKUs reference this table via `sku_id` foreign key.

### 6.3 Indexes

```sql
-- channel_skus
CREATE UNIQUE INDEX idx_channel_sku_marketplace ON channel_skus(channel_sku, marketplace);
CREATE INDEX idx_channel_sku_sku_id ON channel_skus(sku_id);
CREATE INDEX idx_channel_sku_rating ON channel_skus(latest_rating);

-- channel_sku_asin_history  
CREATE INDEX idx_asin_history_channel_sku ON channel_sku_asin_history(channel_sku_id);

-- product_scan_jobs
CREATE INDEX idx_product_scan_status ON product_scan_jobs(status);
CREATE INDEX idx_product_scan_created ON product_scan_jobs(created_at);

-- product_scan_items
CREATE INDEX idx_scan_item_job ON product_scan_items(job_id);
CREATE INDEX idx_scan_item_channel_sku ON product_scan_items(channel_sku_id);
CREATE INDEX idx_scan_item_status ON product_scan_items(status);
```

---

## 7. API Endpoints

### 7.1 Product Scan Jobs API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/product-scans | Create new scan job |
| GET | /api/product-scans | List all scan jobs |
| GET | /api/product-scans/{id} | Get job details |
| GET | /api/product-scans/{id}/results | Get job results (with filters) |
| GET | /api/product-scans/{id}/export/excel | Export results as Excel |
| GET | /api/product-scans/{id}/export/csv | Export results as CSV |
| POST | /api/product-scans/{id}/cancel | Cancel job |
| POST | /api/product-scans/{id}/retry-failed | Retry failed items |
| DELETE | /api/product-scans/{id} | Delete job |

### 7.2 Channel SKUs API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/channel-skus | List all channel SKUs (paginated) |
| GET | /api/channel-skus/{id} | Get channel SKU details |
| GET | /api/channel-skus/{id}/history | Get ASIN change history |
| GET | /api/channel-skus/export | Export all listings |
| POST | /api/channel-skus/bulk-scan | Queue selected for re-scan |

### 7.3 Request/Response Examples

#### Create Scan Job

**Request:**
```json
POST /api/product-scans
{
  "job_name": "December Filter Check",
  "marketplace": "com",
  "skip_header": true,
  "listings": [
    {"sku": "HA-WF2-FLT", "channel_sku": "HA-WF2-FLT", "asin": "B0106TGBCA"},
    {"sku": "HA-WF2-FLT", "channel_sku": "HA-WF2-FLT-2PK", "asin": "B0106TGBY8"}
  ]
}
```

**Response:**
```json
{
  "job_id": 42,
  "job_name": "December Filter Check",
  "status": "queued",
  "total_listings": 2,
  "estimated_time_minutes": 5,
  "message": "Job queued successfully"
}
```

#### Get Job Results

**Request:**
```
GET /api/product-scans/42/results?sort=rating&order=asc&sku=HA-WF2-FLT
```

**Response:**
```json
{
  "job_id": 42,
  "job_name": "December Filter Check",
  "status": "completed",
  "marketplace": "com",
  "summary": {
    "total": 7,
    "completed": 7,
    "failed": 0,
    "average_rating": 4.3,
    "total_reviews": 523
  },
  "results": [
    {
      "sku": "HA-WF2-FLT",
      "channel_sku": "HA-WF2-FLT-2PK-DL1",
      "asin": "B00YU18HI2",
      "rating": 4.1,
      "review_count": 23,
      "status": "completed",
      "product_title": "Replacement Water Filter..."
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total_pages": 1,
    "total_results": 7
  }
}
```

---

## 8. UI/UX Specifications

### 8.1 New Scan Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Channel SKU Metrics > New Scan                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Job Name: [________________________]                           │
│                                                                 │
│  Marketplace: [Amazon.com (com)     ▼]                         │
│                                                                 │
│  ☐ Skip header row                                              │
│                                                                 │
│  ┌─── Input Method ───────────────────────────────────────────┐ │
│  │  [Paste Data]  [Upload CSV]                                │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │                                                            │ │
│  │  SKU          Channel SKU        ASIN                      │ │
│  │  HA-WF2-FLT   HA-WF2-FLT        B0106TGBCA                │ │
│  │  HA-WF2-FLT   HA-WF2-FLT-2PK    B0106TGBY8                │ │
│  │  ...                                                       │ │
│  │                                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  Detected: 7 listings (tab-separated)                           │
│                                                                 │
│  [Start Scan]                                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Results Table Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  December Filter Check                          [Completed ✓]   │
│  Marketplace: Amazon.com | Scraped: Dec 2, 2024                │
├─────────────────────────────────────────────────────────────────┤
│  Summary: 7 listings | Avg Rating: 4.3 | Total Reviews: 523    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [All Results (7)]  [Failed (0)]                               │
│                                                                 │
│  Search: [_______________]  SKU: [All ▼]  Rating: [1.0 ═══ 5.0]│
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ SKU▼        │ Channel SKU    │ ASIN       │ Rating▼│Reviews││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ HA-WF2-FLT  │ HA-WF2-FLT     │ B0106TGBCA │ 4.5    │ 127   ││
│  │ HA-WF2-FLT  │ HA-WF2-FLT-2PK │ B0106TGBY8 │ 4.3    │ 52    ││
│  │ HA-WF2-FLT  │ HA-WF2-FLT-3PK │ B0106TGCMO │ 4.4    │ 89    ││
│  │ ...                                                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  [Export Excel]  [Export CSV]  [Copy Table]                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 All Listings Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Channel SKU Metrics > All Listings                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Total: 1,247 Channel SKUs across 3 marketplaces               │
│                                                                 │
│  Search: [_______________]                                      │
│  Marketplace: [All ▼]  SKU: [All ▼]  Rating: [1.0 ═══ 5.0]     │
│                                                                 │
│  [☐ Select All]  [Re-scan Selected]  [Export All]              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │☐│ SKU         │ Channel SKU  │ ASIN       │ MP  │Rating│Rev ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │☐│ HA-WF2-FLT  │ HA-WF2-FLT   │ B0106TGBCA │ com │ 4.5  │127 ││
│  │☐│ HA-WF2-FLT  │ HA-WF2-FLT   │ B0XXXXXXXX │ ca  │ 4.2  │ 31 ││
│  │☐│ HA-WF2-FLT  │ HA-WF2-FLT-2P│ B0106TGBY8 │ com │ 4.3 ⟳│ 52 ││
│  │ ...                                                        ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ⟳ = ASIN changed (hover for details)                          │
│                                                                 │
│  Page 1 of 25  [< Prev] [Next >]                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.4 ASIN History Modal

When user clicks the history icon (⟳):

```
┌────────────────────────────────────────────────┐
│  ASIN History: HA-WF2-FLT-2PK (Amazon.com)    │
├────────────────────────────────────────────────┤
│                                                │
│  Current ASIN: B0106TGBY8                      │
│                                                │
│  History:                                      │
│  ┌────────────────────────────────────────────┐│
│  │ Date         │ ASIN       │ Changed By     ││
│  ├────────────────────────────────────────────┤│
│  │ Dec 2, 2024  │ B0106TGBY8 │ Dec Scan Job   ││
│  │ Nov 15, 2024 │ B0OLDXXXXX │ Nov Scan Job   ││
│  │ Oct 1, 2024  │ B0FIRSTXXX │ Initial Import ││
│  └────────────────────────────────────────────┘│
│                                                │
│                              [Close]           │
└────────────────────────────────────────────────┘
```

---

## 9. Future Considerations

### 9.1 Scheduled Scans (Next Phase)

- Schedule specific Channel SKU sets for weekly/monthly re-scan
- Define scan schedules in Settings
- Email/notification when scheduled scan completes
- Alert if ratings drop below threshold

### 9.2 Historical Trends

- Track rating/review changes over time
- Line charts showing trends per Channel SKU
- "Health dashboard" showing improving vs declining listings

### 9.3 Competitor Listings Research

- Separate section for competitor ASIN research
- Compare competitor ratings/reviews to own listings
- Track competitor performance over time

### 9.4 Additional Product Data

- Price tracking
- Inventory/availability status
- Buy Box ownership
- Best Seller Rank
- Image/content auditing

---

## 10. Appendix

### 10.1 Apify Actor Reference

**Actor ID:** `axesso_data~amazon-product-details-scraper`  
**Documentation:** https://apify.com/axesso_data/amazon-product-details-scraper

### 10.2 Sample Input Formats

**Tab-separated (from Excel copy):**
```
SKU	Channel SKU	ASIN
HA-WF2-FLT	HA-WF2-FLT	B0106TGBCA
HA-WF2-FLT	HA-WF2-FLT-2PK	B0106TGBY8
```

**Comma-separated (CSV):**
```
SKU,Channel SKU,ASIN
HA-WF2-FLT,HA-WF2-FLT,B0106TGBCA
HA-WF2-FLT,HA-WF2-FLT-2PK,B0106TGBY8
```

### 10.3 Sample Apify Input

```json
{
  "urls": [
    "https://www.amazon.com/dp/B0106TGBCA",
    "https://www.amazon.com/dp/B0106TGBY8",
    "https://www.amazon.com/dp/B00YU18HI2"
  ]
}
```

### 10.4 Sample Output Parsing

**Raw Apify Response:**
```json
{
  "statusCode": 200,
  "statusMessage": "FOUND",
  "asin": "B0106TGBCA",
  "title": "Water Filter Replacement...",
  "productRating": "4.5 out of 5 stars",
  "countReview": 127
}
```

**Parsed for Storage:**
```json
{
  "asin": "B0106TGBCA",
  "title": "Water Filter Replacement...",
  "rating": 4.5,
  "review_count": 127
}
```

### 10.5 Error Handling

| Apify Status | Action |
|--------------|--------|
| statusCode: 200, statusMessage: "FOUND" | Success - store data |
| statusCode: 404 or statusMessage: "NOT_FOUND" | Mark as failed - "Product not found" |
| statusCode: 503 | Retry with backoff |
| No response | Mark as failed - "Scraping error" |

### 10.6 Integration with Reviews Scraper

Both features share:
- **SKUs table:** Same SKU reference for both competitor reviews and own listings
- **Job queue:** Same background worker processes both job types
- **Settings:** Shared Apify API key and delay settings
- **Navigation:** Unified app with separate sections

---

*— End of Document —*
