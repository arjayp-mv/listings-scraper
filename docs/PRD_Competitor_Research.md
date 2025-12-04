# Product Requirements Document
## Competitor Research Feature

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

This document outlines requirements for the **Competitor Research** feature, enabling comprehensive tracking and analysis of competitor Amazon listings. This feature provides critical market intelligence for pricing decisions, listing optimization, and competitive strategy.

### 1.2 Problem Statement

The company sells products on Amazon with thousands of Channel SKU variations under various Parent SKUs. Key challenges include:

- **Pricing blind spot:** No systematic way to track competitor pricing for the price changer tool
- **Manual research:** Competitor analysis is done manually, consuming significant time
- **No historical data:** Cannot track how competitors change prices, ratings, or content over time
- **Scattered information:** Competitor data isn't linked to specific products, keywords, or listings
- **Pack size complexity:** Competitors sell at various pack sizes, making price comparison difficult

### 1.3 Proposed Solution

A comprehensive competitor research module that:

- Tracks competitor listings grouped by Parent SKU
- Monitors pricing with pack size normalization (unit price calculation)
- Stores competitor content (images, bullets, descriptions) for analysis
- Links competitors to keywords and Channel SKUs
- Provides scheduled monitoring with configurable frequencies
- Offers dashboard with alerts and change tracking
- Exports data for the price changer tool integration

### 1.4 Key Benefits

- **Pricing intelligence:** Feed accurate competitor pricing to price changer tool
- **Time savings:** Automated competitor monitoring replaces manual research
- **Historical insights:** Track competitor changes to understand market dynamics
- **Listing optimization:** Analyze competitor content for improvement ideas
- **Centralized data:** All competitor intelligence in one organized system

---

## 2. Feature Overview

### 2.1 Scope

#### In Scope (This Release)

- Parent SKU management with display names
- Manual competitor ASIN entry with pack size
- Full competitor data scraping via Apify
- Three view modes: List, Comparison Table, Detail
- Keywords as first-class entity with Channel SKU linking
- Configurable monitoring schedules (daily, weekly, every X days)
- Price history tracking (1 year retention)
- Dashboard with alerts and change indicators
- Bulk import competitors via CSV
- Export (CSV, Excel) and API endpoints

#### Out of Scope (Future Phases)

- AI image analysis for competitor listings
- Automated competitor discovery via search results scraper
- Sales/revenue estimation
- Keyword ranking data (Share of Voice, etc.)
- Automated price changer integration (manual export for now)

### 2.2 Apify Actor

**Actor:** `axesso_data~amazon-product-details-scraper`

**Key Output Fields Used:**

| Field | Usage |
|-------|-------|
| title | Product title |
| brand.value | Brand name |
| pastSales | Sales velocity ("100+ bought in past month") |
| countReview | Review count |
| productRating | Rating (parsed to numeric) |
| asin | Confirmed ASIN |
| soldBy | Seller name |
| fulfilledBy | Fulfillment entity |
| sellerId | Seller ID |
| warehouseAvailability | Stock status |
| price | Current price |
| shippingPrice | Shipping cost |
| features | Bullet points array |
| productDescription | Product description |
| mainImage.imageUrl | Main image URL |
| imageUrlList | All image URLs |
| videoUrlList | Video URLs (if any) |
| variations | Variation data |
| categoriesExtended | Category hierarchy |
| reviewInsights | Review analysis data |

### 2.3 Updated Navigation Structure

```
Dashboard | New Scrape | Jobs | Channel SKU Metrics | Competitor Research | SKUs | Settings
                                                    └── Dashboard (Overview)
                                                    └── Parent SKUs
                                                    └── All Competitors
                                                    └── Keywords
                                                    └── Monitoring
```

---

## 3. User Stories

### 3.1 Parent SKU Management

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| CR-01 | As a user, I want to create Parent SKU groups to organize competitors | • Create Parent SKU with required SKU code<br>• Optional display name<br>• Links to existing SKUs table |
| CR-02 | As a user, I want to add pack size to my Channel SKUs | • Free number entry for pack size<br>• Required for unit price calculation |

### 3.2 Competitor Management

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| CR-03 | As a user, I want to add competitors by ASIN | • Enter ASIN + Pack Size + Marketplace<br>• System constructs Amazon URL<br>• Triggers initial scrape |
| CR-04 | As a user, I want to bulk import competitors | • CSV upload with ASIN, Pack Size columns<br>• Validate ASINs before import<br>• Show import preview |
| CR-05 | As a user, I want to see all competitor data | • Full detail view with all scraped fields<br>• Organized in logical tabs |
| CR-06 | As a user, I want to compare competitors side by side | • Spreadsheet-style comparison table<br>• Sortable columns<br>• Key metrics at a glance |

### 3.3 Keywords & Linking

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| CR-07 | As a user, I want to track keywords for a Parent SKU | • Add keywords as separate entities<br>• Keywords belong to Parent SKU + Marketplace |
| CR-08 | As a user, I want to link Channel SKUs to keywords | • Search and select Channel SKUs<br>• Multi-select capability<br>• Bulk import option |
| CR-09 | As a user, I want to link competitors to keywords | • Associate competitors with keywords where found<br>• Same competitor can link to multiple keywords |

### 3.4 Monitoring & Scheduling

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| CR-10 | As a user, I want to schedule competitor monitoring | • Per-ASIN schedule options<br>• Daily, weekly, every X days<br>• Bulk schedule selection |
| CR-11 | As a user, I want to see price changes over time | • Price history chart per competitor<br>• 1 year data retention |

### 3.5 Dashboard & Alerts

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| CR-12 | As a user, I want a dashboard showing competitor changes | • Global dashboard for all Parent SKUs<br>• Per-Parent SKU detailed dashboard |
| CR-13 | As a user, I want to see which competitors changed price | • Visual indicators for changes<br>• Change amount and direction |

### 3.6 Export & Integration

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| CR-14 | As a user, I want to export competitor data for price changer | • CSV/Excel with ASIN, Pack Size, Price, Unit Price<br>• Filterable export |
| CR-15 | As a user, I want API access to competitor data | • REST API endpoints<br>• Filter by Parent SKU, marketplace |

---

## 4. Functional Requirements

### 4.1 Parent SKU Management

Parent SKUs serve as the top-level grouping for competitor research.

#### Parent SKU Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sku_code | VARCHAR(50) | Yes | Parent SKU identifier (e.g., HA-WF2-FLT) |
| display_name | VARCHAR(255) | No | Friendly name (e.g., "WF2 Filters") |
| marketplace | VARCHAR(10) | Yes | Amazon domain code |
| notes | TEXT | No | Internal notes |

#### Parent SKU Features

- Link to existing SKU record if exists
- View all Channel SKUs under this Parent
- View all competitors tracked
- View all keywords tracked
- Dashboard specific to this Parent SKU

### 4.2 Channel SKU Pack Size

Extend Channel SKU (from Channel SKU Metrics) with pack size.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| pack_size | INT | Yes | Number of units (1 for single, 2 for 2-pack, etc.) |

- Required for unit price calculation
- Free number entry (not dropdown)
- Used to match with competitor pack sizes

### 4.3 Competitor Management

#### Adding Competitors

**Single Add:**
- Enter ASIN (10 characters)
- Enter Pack Size (number)
- Select Marketplace (defaults to Parent SKU's marketplace)
- System validates ASIN format
- System constructs URL: `https://www.amazon.{domain}/dp/{ASIN}`
- Triggers immediate scrape

**Bulk Import (CSV):**
```csv
asin,pack_size,notes
B0BKGXQBCB,1,Main competitor
B0D7VBZ3FM,2,Budget option
B00K537MGC,1,Premium brand
```

- Upload CSV file
- Preview before import
- Validate ASINs
- Show duplicates (already tracked)
- Option to update pack size for existing

#### Competitor Data Fields

All fields from Apify scraper stored:

**Core Fields:**
| Field | Display Name | Notes |
|-------|--------------|-------|
| asin | ASIN | Clickable link to Amazon |
| title | Title | Full product title |
| brand | Brand | Extracted from brand.value |
| price | Price | Current listing price |
| shipping_price | Shipping | Shipping cost |
| pack_size | Pack Size | Manually entered |
| unit_price | Unit Price | Calculated: price / pack_size |

**Sales & Reviews:**
| Field | Display Name | Notes |
|-------|--------------|-------|
| past_sales | Sales Velocity | e.g., "100+ bought in past month" |
| review_count | Reviews | Number of reviews |
| rating | Rating | Numeric (e.g., 4.7) |
| review_insights | Review Insights | Structured review analysis |

**Seller Info:**
| Field | Display Name | Notes |
|-------|--------------|-------|
| sold_by | Sold By | Seller name |
| fulfilled_by | Fulfilled By | Fulfillment entity |
| seller_id | Seller ID | Amazon seller ID |
| availability | Availability | Stock status |

**Content:**
| Field | Display Name | Notes |
|-------|--------------|-------|
| features | Bullet Points | Array of feature bullets |
| description | Description | Product description HTML |
| main_image_url | Main Image | Primary product image |
| image_urls | Images | All image URLs as array |
| has_video | Has Video | Boolean |
| video_urls | Video Links | URLs if videos exist |

**Categorization:**
| Field | Display Name | Notes |
|-------|--------------|-------|
| variations_count | Variations | Number of variations |
| variations_types | Variation Types | e.g., "Color, Size" |
| categories | Categories | Array with name and node ID |

### 4.4 Keywords Management

Keywords are first-class entities linked to Parent SKUs.

#### Keyword Fields

| Field | Type | Description |
|-------|------|-------------|
| keyword | VARCHAR(255) | Search term |
| parent_sku_id | FK | Parent SKU this keyword belongs to |
| marketplace | VARCHAR(10) | Amazon domain |
| notes | TEXT | Optional notes |

#### Linking Channel SKUs to Keywords

Multiple ways to link:

1. **Search and Select:** Type Channel SKU, select from results
2. **Multi-Select:** Checkbox selection from list
3. **Select All:** Select all Channel SKUs under Parent SKU
4. **Bulk Import:** CSV with Channel SKU, Keyword pairs

#### Linking Competitors to Keywords

- When adding competitor, optionally specify "found via keyword"
- Same competitor can be linked to multiple keywords
- Helps track which competitors appear for which searches

### 4.5 Monitoring & Scheduling

#### Schedule Options

| Option | Description |
|--------|-------------|
| Daily | Scrape every day |
| Every 2 Days | Scrape every other day |
| Every 3 Days | Scrape every 3 days |
| Weekly | Scrape once per week |
| Every X Days | Custom interval (user specified) |
| Manual Only | No automatic scraping |

#### Schedule Management

- Set schedule per competitor ASIN
- Bulk select multiple competitors, apply same schedule
- View all scheduled scrapes in Monitoring tab
- Pause/resume schedules
- Override next scrape time

#### Scrape Queue

- Scheduled scrapes added to shared job queue
- Respects Apify delay settings
- Groups scrapes by Parent SKU for efficiency
- Retry logic for failed scrapes

### 4.6 Price History

#### Data Tracked

| Field | Description |
|-------|-------------|
| price | Listing price at time of scrape |
| shipping_price | Shipping at time of scrape |
| unit_price | Calculated unit price |
| availability | Stock status |
| review_count | Reviews at time |
| rating | Rating at time |
| scraped_at | Timestamp |

#### Retention

- **Duration:** 1 year rolling window
- **Cleanup:** Automated purge of data older than 1 year
- **Export:** Full history exportable before purge

#### Price History Chart

- Line chart showing price over time
- Toggle between price and unit price
- Compare multiple competitors on same chart
- Zoom to date ranges

### 4.7 Dashboard & Alerts

#### Global Dashboard (All Parent SKUs)

Shows overview across all tracked competitors:

**Summary Cards:**
- Total Parent SKUs tracked
- Total Competitors tracked
- Competitors with price changes (last 7 days)
- Competitors with rating changes
- Upcoming scheduled scrapes

**Recent Changes Table:**
| Column | Description |
|--------|-------------|
| Parent SKU | Which product group |
| Competitor | ASIN and title |
| Change Type | Price ↓, Price ↑, Rating change, New competitor |
| Previous | Old value |
| Current | New value |
| Change % | Percentage change |
| When | Timestamp |

**Filters:**
- Date range
- Change type
- Parent SKU
- Marketplace

#### Parent SKU Dashboard

Detailed view for specific Parent SKU:

**Summary:**
- Your listings count
- Competitors count
- Keywords tracked
- Last scraped date
- Average competitor price
- Price range (min - max)
- Your price position (cheapest, mid-range, premium)

**Price Position Chart:**
- Visual showing where your listings fall vs competitors
- Grouped by pack size

**Recent Changes:**
- Same as global but filtered to this Parent SKU
- More detailed change tracking

**Alerts Section:**
- Competitors that dropped price significantly (>10%)
- Competitors that raised price
- Competitors that went out of stock
- New reviews or rating changes

### 4.8 Views

#### List View

Quick overview of all competitors for a Parent SKU.

**Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│ [>] B0BKGXQBCB                                                  │
│     HolaHatha 2, 3, 5, 8 Pound Neoprene Dumbbell...            │
│     $49.99 | 2-Pack | $25.00/unit                              │
│     [img][img][img][img][img][img][img][img]                   │
├─────────────────────────────────────────────────────────────────┤
│ [>] B0D7VBZ3FM                                                  │
│     YTX5L-BS Motorcycle Battery, 12V 4Ah Rechargeable...       │
│     $20.99 | Single | $20.99/unit                              │
│     [img][img][img][img][img][img][img][img]                   │
└─────────────────────────────────────────────────────────────────┘
```

**Features:**
- Expandable rows (click arrow to expand)
- ASIN as clickable link
- Title (truncated)
- Price, Pack Size, Unit Price
- Image thumbnails in row
- Quick actions: View Detail, Edit, Delete

#### Comparison Table View

Spreadsheet-style side-by-side comparison.

**Columns:**
| Column | Sortable | Description |
|--------|----------|-------------|
| Image | No | Main product image thumbnail |
| Brand | Yes | Brand name |
| ASIN | Yes | Clickable link |
| Title | No | Truncated title |
| Pack Size | Yes | Units per listing |
| Price | Yes | Current price |
| Unit Price | Yes | Price per unit |
| Shipping | Yes | Shipping cost |
| Rating | Yes | Star rating |
| Reviews | Yes | Review count |
| Sales | Yes | Past sales text |
| Seller | Yes | Sold by |
| Fulfillment | Yes | FBA/FBM/AMZ |
| Availability | Yes | Stock status |
| Variations | Yes | Variation count |
| Last Updated | Yes | Last scrape date |

**Features:**
- Sort by any column
- Filter by pack size, price range, rating
- Sticky first column (image + ASIN)
- Horizontal scroll for many columns
- Export visible data
- Click row to open detail view

#### Detail View

Full competitor information with tabbed layout.

**Header:**
```
┌─────────────────────────────────────────────────────────────────┐
│ B0BKGXQBCB  [Open on Amazon ↗]                                 │
│ HolaHatha 2, 3, 5, 8, and 10 Pound Neoprene Dumbbell...       │
│ $49.99 | Brand: HolaHatha | ⭐ 4.7 (3,511 reviews)             │
│                                                                 │
│ Pack Size: 2  |  Unit Price: $25.00  |  Shipping: Free         │
│ Sold by: Spreetail  |  Fulfilled by: Spreetail                 │
│ Status: In Stock  |  100+ bought in past month                 │
└─────────────────────────────────────────────────────────────────┘
```

**Tabs:**

**Tab 1: Images**
- Main image (large)
- Secondary images (grid)
- Click to enlarge
- Has Video indicator with link if available

**Tab 2: Title & Bullets**
- Full product title
- Bullet points (features) displayed as list
- Each bullet on separate line for readability

**Tab 3: Description**
- Full product description
- Rendered HTML

**Tab 4: Reviews**
- Rating with star visualization
- Review count
- Review insights from Apify (structured analysis)

**Tab 5: Variations**
- Has Variations: Yes/No
- Variation count
- Variation types (e.g., "Color, Size")

**Tab 6: Categories**
- Category path with node IDs
- Format: "Category Name (node: 12345)"
- Multiple categories if applicable

**Tab 7: Price History**
- Line chart of price over time
- Data points for each scrape
- Toggle unit price view

**Tab 8: Seller Info**
- Sold By
- Fulfilled By
- Seller ID (clickable to Amazon seller page)
- Availability status

### 4.9 Export & API

#### Export Options

**CSV Export:**
- All competitor data for Parent SKU
- Filterable (marketplace, date range)
- Custom column selection

**Excel Export:**
- Same as CSV but .xlsx format
- Multiple sheets (competitors, price history, keywords)

**Price Changer Export:**
Specific format for price changer tool:
```csv
asin,pack_size,price,shipping_price,unit_price,brand,availability,last_updated
B0BKGXQBCB,2,49.99,0,25.00,HolaHatha,In Stock,2024-12-02
```

#### API Endpoints

Full REST API for programmatic access (see Section 7).

---

## 5. Technical Architecture

### 5.1 System Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│  Competitor Research Module                                      │
│  ├── Dashboard (Global + Per-Parent SKU)                        │
│  ├── Parent SKU Management                                       │
│  ├── Competitor Views (List, Table, Detail)                     │
│  ├── Keywords Management                                         │
│  └── Monitoring & Scheduling                                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │ REST API
┌─────────────────────────────┴───────────────────────────────────┐
│                         BACKEND                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Reviews Scraper │  │ Channel SKU     │  │ Competitor      │  │
│  │    Service      │  │ Metrics Service │  │ Research Service│  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
│           │                    │                     │           │
│           └────────────────────┼─────────────────────┘           │
│                                │                                 │
│                     ┌──────────┴──────────┐                     │
│                     │   Scheduler Service │  ← Handles scheduled│
│                     │   (Background Jobs) │    competitor scrapes│
│                     └──────────┬──────────┘                     │
│                                │                                 │
│                     ┌──────────┴──────────┐                     │
│                     │     Job Queue       │                     │
│                     │     (shared)        │                     │
│                     └─────────────────────┘                     │
└──────────┬──────────────────────────────────────────┬───────────┘
           │                                          │
           ▼                                          ▼
    ┌──────────────┐                         ┌────────────────┐
    │   MySQL DB   │                         │   Apify API    │
    │  (extended)  │                         │ Product Actor  │
    └──────────────┘                         └────────────────┘
```

### 5.2 Scheduler Service

New background service for scheduled competitor scrapes:

```python
class CompetitorSchedulerService:
    """
    Manages scheduled competitor scraping.
    
    Runs every hour to check for due scrapes.
    """
    
    def check_scheduled_scrapes(self):
        """Find competitors due for scraping."""
        due_competitors = db.query(Competitor).filter(
            Competitor.next_scrape_at <= datetime.utcnow(),
            Competitor.schedule != 'manual'
        ).all()
        
        for competitor in due_competitors:
            self.queue_scrape(competitor)
            self.update_next_scrape(competitor)
    
    def update_next_scrape(self, competitor):
        """Calculate next scrape time based on schedule."""
        intervals = {
            'daily': timedelta(days=1),
            'every_2_days': timedelta(days=2),
            'every_3_days': timedelta(days=3),
            'weekly': timedelta(weeks=1),
        }
        
        if competitor.schedule.startswith('every_'):
            days = int(competitor.schedule.split('_')[1])
            interval = timedelta(days=days)
        else:
            interval = intervals.get(competitor.schedule)
        
        competitor.next_scrape_at = datetime.utcnow() + interval
```

### 5.3 Unit Price Calculation

```python
def calculate_unit_price(price: float, pack_size: int) -> float:
    """Calculate price per unit."""
    if pack_size <= 0:
        return price
    return round(price / pack_size, 2)
```

### 5.4 Data Parsing

```python
def parse_competitor_data(apify_response: dict) -> dict:
    """Parse Apify response into competitor fields."""
    
    # Parse rating from string
    rating_str = apify_response.get('productRating', '')
    rating = None
    if rating_str:
        match = re.search(r'(\d+\.?\d*)\s*out of', rating_str)
        rating = float(match.group(1)) if match else None
    
    # Extract brand
    brand = None
    brand_data = apify_response.get('brand', {})
    if isinstance(brand_data, dict):
        brand = brand_data.get('value')
    
    # Parse variations
    variations = apify_response.get('variations', [])
    variations_count = len(variations) if variations else 0
    variations_types = []
    if variations:
        for var in variations:
            var_type = var.get('variationType')
            if var_type and var_type not in variations_types:
                variations_types.append(var_type)
    
    # Check for videos
    video_urls = apify_response.get('videoUrlList', [])
    has_video = len(video_urls) > 0 if video_urls else False
    
    # Parse categories
    categories = []
    categories_extended = apify_response.get('categoriesExtended', [])
    for cat in categories_extended:
        cat_name = cat.get('name', '')
        cat_node = cat.get('node', '')
        categories.append({
            'name': cat_name,
            'node': cat_node,
            'display': f"{cat_name} (node: {cat_node})"
        })
    
    return {
        'asin': apify_response.get('asin'),
        'title': apify_response.get('title'),
        'brand': brand,
        'price': apify_response.get('price'),
        'shipping_price': apify_response.get('shippingPrice', 0),
        'past_sales': apify_response.get('pastSales'),
        'review_count': apify_response.get('countReview'),
        'rating': rating,
        'sold_by': apify_response.get('soldBy'),
        'fulfilled_by': apify_response.get('fulfilledBy'),
        'seller_id': apify_response.get('sellerId'),
        'availability': apify_response.get('warehouseAvailability'),
        'features': apify_response.get('features', []),
        'description': apify_response.get('productDescription'),
        'main_image_url': apify_response.get('mainImage', {}).get('imageUrl'),
        'image_urls': apify_response.get('imageUrlList', []),
        'has_video': has_video,
        'video_urls': video_urls,
        'variations_count': variations_count,
        'variations_types': ', '.join(variations_types),
        'categories': categories,
        'review_insights': apify_response.get('reviewInsights'),
    }
```

---

## 6. Database Schema

### 6.1 New Tables

#### competitor_parent_skus

Top-level grouping for competitor tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT PK AUTO | Primary key |
| sku_id | BIGINT FK NULL | Link to skus table (optional) |
| sku_code | VARCHAR(50) | Parent SKU code (required) |
| display_name | VARCHAR(255) | Friendly name (optional) |
| marketplace | VARCHAR(10) | Amazon domain code |
| notes | TEXT | Internal notes |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update |

**Unique:** (sku_code, marketplace)

#### competitors

Individual competitor ASINs being tracked.

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT PK AUTO | Primary key |
| parent_sku_id | BIGINT FK | Reference to competitor_parent_skus |
| asin | VARCHAR(15) | Amazon ASIN |
| marketplace | VARCHAR(10) | Amazon domain code |
| pack_size | INT | Units per listing |
| notes | TEXT | Internal notes |
| schedule | VARCHAR(20) | Monitoring schedule |
| next_scrape_at | TIMESTAMP | Next scheduled scrape |
| is_active | BOOLEAN | Active tracking flag |
| created_at | TIMESTAMP | When added |
| updated_at | TIMESTAMP | Last update |

**Unique:** (asin, marketplace, parent_sku_id)

#### competitor_data

Latest scraped data for each competitor.

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT PK AUTO | Primary key |
| competitor_id | BIGINT FK | Reference to competitors |
| title | VARCHAR(500) | Product title |
| brand | VARCHAR(100) | Brand name |
| price | DECIMAL(10,2) | Current price |
| shipping_price | DECIMAL(10,2) | Shipping cost |
| unit_price | DECIMAL(10,2) | Calculated unit price |
| past_sales | VARCHAR(100) | Sales velocity text |
| review_count | INT | Number of reviews |
| rating | DECIMAL(2,1) | Star rating |
| sold_by | VARCHAR(255) | Seller name |
| fulfilled_by | VARCHAR(255) | Fulfillment entity |
| seller_id | VARCHAR(50) | Amazon seller ID |
| availability | VARCHAR(100) | Stock status |
| features | JSON | Bullet points array |
| description | TEXT | Product description |
| main_image_url | VARCHAR(500) | Main image URL |
| image_urls | JSON | All image URLs |
| has_video | BOOLEAN | Has video content |
| video_urls | JSON | Video URLs |
| variations_count | INT | Number of variations |
| variations_types | VARCHAR(255) | Variation type names |
| categories | JSON | Category hierarchy |
| review_insights | JSON | Review analysis |
| scraped_at | TIMESTAMP | When data was scraped |

#### competitor_price_history

Historical price tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT PK AUTO | Primary key |
| competitor_id | BIGINT FK | Reference to competitors |
| price | DECIMAL(10,2) | Price at time |
| shipping_price | DECIMAL(10,2) | Shipping at time |
| unit_price | DECIMAL(10,2) | Unit price at time |
| availability | VARCHAR(100) | Stock status at time |
| review_count | INT | Reviews at time |
| rating | DECIMAL(2,1) | Rating at time |
| scraped_at | TIMESTAMP | When scraped |

**Index:** (competitor_id, scraped_at)
**Retention:** 1 year rolling

#### competitor_keywords

Keywords tracked for competitor research.

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT PK AUTO | Primary key |
| parent_sku_id | BIGINT FK | Reference to competitor_parent_skus |
| keyword | VARCHAR(255) | Search term |
| marketplace | VARCHAR(10) | Amazon domain |
| notes | TEXT | Internal notes |
| created_at | TIMESTAMP | When added |

**Unique:** (parent_sku_id, keyword, marketplace)

#### keyword_channel_sku_links

Links Channel SKUs to keywords.

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT PK AUTO | Primary key |
| keyword_id | BIGINT FK | Reference to competitor_keywords |
| channel_sku_id | BIGINT FK | Reference to channel_skus |
| created_at | TIMESTAMP | When linked |

**Unique:** (keyword_id, channel_sku_id)

#### keyword_competitor_links

Links competitors to keywords (where they were found).

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT PK AUTO | Primary key |
| keyword_id | BIGINT FK | Reference to competitor_keywords |
| competitor_id | BIGINT FK | Reference to competitors |
| created_at | TIMESTAMP | When linked |

**Unique:** (keyword_id, competitor_id)

#### competitor_scrape_jobs

Job tracking for competitor scraping.

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT PK AUTO | Primary key |
| job_type | ENUM | 'manual', 'scheduled', 'bulk_import' |
| parent_sku_id | BIGINT FK NULL | If scoped to Parent SKU |
| status | ENUM | queued, running, completed, failed |
| total_competitors | INT | Number to scrape |
| completed_count | INT | Successfully scraped |
| failed_count | INT | Failed scrapes |
| error_message | TEXT | Error if failed |
| created_at | TIMESTAMP | Job creation |
| started_at | TIMESTAMP | Processing start |
| completed_at | TIMESTAMP | Completion time |

### 6.2 Extended Tables

#### channel_skus (add column)

| Column | Type | Description |
|--------|------|-------------|
| pack_size | INT DEFAULT 1 | Units per listing |

### 6.3 Indexes

```sql
-- competitor_parent_skus
CREATE UNIQUE INDEX idx_parent_sku_marketplace ON competitor_parent_skus(sku_code, marketplace);

-- competitors
CREATE UNIQUE INDEX idx_competitor_asin ON competitors(asin, marketplace, parent_sku_id);
CREATE INDEX idx_competitor_parent ON competitors(parent_sku_id);
CREATE INDEX idx_competitor_schedule ON competitors(schedule, next_scrape_at);

-- competitor_data
CREATE INDEX idx_competitor_data_competitor ON competitor_data(competitor_id);

-- competitor_price_history
CREATE INDEX idx_price_history_competitor ON competitor_price_history(competitor_id, scraped_at);
CREATE INDEX idx_price_history_date ON competitor_price_history(scraped_at);

-- competitor_keywords
CREATE UNIQUE INDEX idx_keyword_unique ON competitor_keywords(parent_sku_id, keyword, marketplace);

-- links
CREATE INDEX idx_keyword_channel_link ON keyword_channel_sku_links(keyword_id);
CREATE INDEX idx_keyword_competitor_link ON keyword_competitor_links(keyword_id);
```

---

## 7. API Endpoints

### 7.1 Parent SKU Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/competitor-research/parent-skus | List all Parent SKUs |
| POST | /api/competitor-research/parent-skus | Create Parent SKU |
| GET | /api/competitor-research/parent-skus/{id} | Get Parent SKU details |
| PUT | /api/competitor-research/parent-skus/{id} | Update Parent SKU |
| DELETE | /api/competitor-research/parent-skus/{id} | Delete Parent SKU |
| GET | /api/competitor-research/parent-skus/{id}/dashboard | Get Parent SKU dashboard data |

### 7.2 Competitor Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/competitor-research/competitors | List all competitors (with filters) |
| POST | /api/competitor-research/competitors | Add single competitor |
| POST | /api/competitor-research/competitors/bulk | Bulk import competitors |
| GET | /api/competitor-research/competitors/{id} | Get competitor details |
| PUT | /api/competitor-research/competitors/{id} | Update competitor |
| DELETE | /api/competitor-research/competitors/{id} | Delete competitor |
| POST | /api/competitor-research/competitors/{id}/scrape | Trigger manual scrape |
| GET | /api/competitor-research/competitors/{id}/history | Get price history |

### 7.3 Keyword Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/competitor-research/keywords | List all keywords |
| POST | /api/competitor-research/keywords | Create keyword |
| GET | /api/competitor-research/keywords/{id} | Get keyword details |
| PUT | /api/competitor-research/keywords/{id} | Update keyword |
| DELETE | /api/competitor-research/keywords/{id} | Delete keyword |
| POST | /api/competitor-research/keywords/{id}/link-channel-skus | Link Channel SKUs |
| POST | /api/competitor-research/keywords/{id}/link-competitors | Link competitors |

### 7.4 Schedule Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/competitor-research/schedules | List all scheduled scrapes |
| PUT | /api/competitor-research/competitors/{id}/schedule | Update competitor schedule |
| POST | /api/competitor-research/schedules/bulk | Bulk update schedules |

### 7.5 Dashboard Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/competitor-research/dashboard | Global dashboard data |
| GET | /api/competitor-research/dashboard/changes | Recent changes across all |

### 7.6 Export Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/competitor-research/export/csv | Export to CSV |
| GET | /api/competitor-research/export/excel | Export to Excel |
| GET | /api/competitor-research/export/price-changer | Export for price changer |

### 7.7 Request/Response Examples

#### Add Competitor

**Request:**
```json
POST /api/competitor-research/competitors
{
  "parent_sku_id": 5,
  "asin": "B0BKGXQBCB",
  "pack_size": 2,
  "marketplace": "com",
  "schedule": "weekly",
  "keyword_ids": [12, 15],
  "notes": "Main competitor"
}
```

**Response:**
```json
{
  "id": 42,
  "asin": "B0BKGXQBCB",
  "marketplace": "com",
  "pack_size": 2,
  "schedule": "weekly",
  "next_scrape_at": "2024-12-09T00:00:00Z",
  "status": "scraping",
  "message": "Competitor added. Initial scrape in progress."
}
```

#### Get Competitors with Data

**Request:**
```
GET /api/competitor-research/competitors?parent_sku_id=5&sort=unit_price&order=asc
```

**Response:**
```json
{
  "competitors": [
    {
      "id": 42,
      "asin": "B0BKGXQBCB",
      "amazon_url": "https://www.amazon.com/dp/B0BKGXQBCB",
      "pack_size": 2,
      "schedule": "weekly",
      "data": {
        "title": "HolaHatha 2, 3, 5, 8 Pound Neoprene Dumbbell...",
        "brand": "HolaHatha",
        "price": 49.99,
        "shipping_price": 0,
        "unit_price": 25.00,
        "rating": 4.7,
        "review_count": 3511,
        "availability": "In Stock",
        "scraped_at": "2024-12-02T10:30:00Z"
      },
      "keywords": ["dumbbell set", "neoprene weights"]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 23
  }
}
```

#### Export for Price Changer

**Request:**
```
GET /api/competitor-research/export/price-changer?parent_sku_id=5
```

**Response (CSV):**
```csv
asin,pack_size,price,shipping_price,unit_price,brand,availability,last_updated
B0BKGXQBCB,2,49.99,0,25.00,HolaHatha,In Stock,2024-12-02
B0D7VBZ3FM,1,20.99,0,20.99,Autocessking,In Stock,2024-12-02
```

---

## 8. UI/UX Specifications

### 8.1 Navigation

```
Competitor Research
├── Dashboard                    ← Global overview
├── Parent SKUs                  ← List/manage Parent SKUs
│   └── [Parent SKU Detail]      ← Competitors, keywords for one Parent
├── All Competitors              ← Search across all
├── Keywords                     ← Manage keywords
└── Monitoring                   ← View/manage schedules
```

### 8.2 Dashboard Page

**Global Dashboard:**
```
┌─────────────────────────────────────────────────────────────────┐
│  Competitor Research Dashboard                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Parent   │ │Competitors│ │  Price   │ │ Upcoming │          │
│  │ SKUs     │ │ Tracked   │ │ Changes  │ │ Scrapes  │          │
│  │   15     │ │   342     │ │  23 ↓7d  │ │  45 24h  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│                                                                 │
│  Recent Changes (Last 7 Days)                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Parent SKU │ Competitor    │ Change      │ From  │ To      ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ HA-WF2-FLT │ B0BKGXQBCB   │ Price ↓     │$49.99 │ $44.99  ││
│  │ HA-WF2-FLT │ B0D7VBZ3FM   │ Price ↑     │$18.99 │ $20.99  ││
│  │ HA-ABC-123 │ B00K537MGC   │ Out of Stock│ In    │ Out     ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  [View All Changes]                                            │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 Parent SKU List Page

```
┌─────────────────────────────────────────────────────────────────┐
│  Parent SKUs                               [+ Add Parent SKU]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Search: [_______________]  Marketplace: [All ▼]               │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ SKU Code     │ Display Name  │ MP  │Competitors│ Keywords  ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ HA-WF2-FLT   │ WF2 Filters   │ com │    23     │    5      ││
│  │ HA-ABC-123   │ ABC Product   │ com │    15     │    3      ││
│  │ HA-XYZ-789   │ -             │ ca  │     8     │    2      ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.4 Parent SKU Detail Page

```
┌─────────────────────────────────────────────────────────────────┐
│  HA-WF2-FLT (WF2 Filters)                    Amazon.com        │
│  Your Listings: 147 | Competitors: 23 | Keywords: 5            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Dashboard] [Competitors] [Your Listings] [Keywords]          │
│                                                                 │
│  ═══════════════════════════════════════════════════════════   │
│  DASHBOARD TAB                                                  │
│  ═══════════════════════════════════════════════════════════   │
│                                                                 │
│  Price Overview                                                 │
│  ┌───────────────────────────────────────┐                     │
│  │ Your Range: $12.99 - $45.99           │                     │
│  │ Competitor Range: $10.99 - $52.99     │                     │
│  │ Avg Competitor Unit Price: $13.45     │                     │
│  └───────────────────────────────────────┘                     │
│                                                                 │
│  Recent Alerts                                                  │
│  ⚠️ Competitor B0BKGXQBCB dropped price 10% ($49.99 → $44.99)  │
│  ⚠️ Competitor B00K537MGC went out of stock                    │
│  ℹ️ Competitor B0D7VBZ3FM gained 50 new reviews                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.5 Competitors Tab - List View

```
┌─────────────────────────────────────────────────────────────────┐
│  Competitors (23)                      [+ Add] [Import CSV]     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  View: [● List] [○ Table] [○ Detail]                           │
│                                                                 │
│  Search: [___________]  Pack Size: [All ▼]  Sort: [Price ▼]    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ [>] B0BKGXQBCB ↗                                    [⋮]    ││
│  │     HolaHatha 2, 3, 5, 8, and 10 Pound Neoprene Dumbbell   ││
│  │     $49.99 | 2-Pack | $25.00/unit | ⭐4.7 (3,511)           ││
│  │     [img][img][img][img][img][img][img][img]                ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ [>] B0D7VBZ3FM ↗                                    [⋮]    ││
│  │     YTX5L-BS Motorcycle Battery, 12V 4Ah Rechargeable...   ││
│  │     $20.99 | Single | $20.99/unit | ⭐4.4 (514)             ││
│  │     [img][img][img][img][img][img][img][img]                ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  [Export Excel] [Export CSV] [Export for Price Changer]        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.6 Competitors Tab - Comparison Table View

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Competitors (23)                                    [+ Add] [Import CSV]        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  View: [○ List] [● Table] [○ Detail]                                            │
│                                                                                  │
│  Pack Size: [All ▼]  Price Range: [$0 ════ $100]     [Export ▼]                 │
│                                                                                  │
│  ┌──────────────────────────────────────────────────────────────────────────────┐│
│  │     │ Image│Brand    │ASIN       │Pack│Price │Unit$ │Rating│Reviews│Seller  ││
│  ├──────────────────────────────────────────────────────────────────────────────┤│
│  │  1  │[img] │HolaHatha│B0BKGXQBCB │ 2  │$49.99│$25.00│ 4.7  │ 3,511 │Spreetail│
│  │  2  │[img] │Autoces..│B0D7VBZ3FM │ 1  │$20.99│$20.99│ 4.4  │   514 │Amazon  ││
│  │  3  │[img] │MightyMax│B00K537MGC │ 1  │$19.99│$19.99│ 4.3  │ 2,132 │MightyMax│
│  │  4  │[img] │UPLUS    │B09KGYVWJN │ 1  │$23.99│$23.99│ 4.4  │   766 │China   ││
│  │ ... │      │         │           │    │      │      │      │       │        ││
│  └──────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ← Scroll horizontally for more columns →                                       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 8.7 Competitor Detail View

```
┌─────────────────────────────────────────────────────────────────┐
│  B0BKGXQBCB                              [Open on Amazon ↗]     │
│  HolaHatha 2, 3, 5, 8, and 10 Pound Neoprene Dumbbell Free...  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  $49.99 | Pack: 2 | Unit: $25.00 | Shipping: Free              │
│  ⭐ 4.7 (3,511 reviews) | 100+ bought in past month            │
│  Brand: HolaHatha | Sold by: Spreetail | Fulfilled by: Spreetail│
│  Status: In Stock | Schedule: Weekly (Next: Dec 9)             │
│                                                                 │
│  [Images] [Title & Bullets] [Description] [Reviews] [Variations]│
│  [Categories] [Price History] [Seller Info]                     │
│                                                                 │
│  ═══════════════════════════════════════════════════════════   │
│  IMAGES TAB                                                     │
│  ═══════════════════════════════════════════════════════════   │
│                                                                 │
│  ┌─────────────────────┐                                       │
│  │                     │  📹 Has Video [Watch on Amazon ↗]     │
│  │   [Main Image]      │                                       │
│  │                     │                                       │
│  │                     │                                       │
│  └─────────────────────┘                                       │
│                                                                 │
│  [img] [img] [img] [img] [img] [img] [img] [img]               │
│                                                                 │
│  ═══════════════════════════════════════════════════════════   │
│  TITLE & BULLETS TAB                                           │
│  ═══════════════════════════════════════════════════════════   │
│                                                                 │
│  Title:                                                         │
│  HolaHatha 2, 3, 5, 8, and 10 Pound Neoprene Dumbbell Free    │
│  Hand Weight Set with Rack, Ideal for Home Exercises to Gain   │
│  Tone and Definition, Pastel                                   │
│                                                                 │
│  Bullet Points:                                                 │
│  • COMPLETE DUMBBELL SET: Includes 2, 3, 5, 8, and 10 pound   │
│    dumbbells with a convenient storage rack                    │
│  • NEOPRENE COATING: Comfortable grip and floor protection    │
│  • ERGONOMIC DESIGN: Easy to hold during workouts             │
│  • VERSATILE USE: Perfect for home gym, office, travel        │
│  • DURABLE CONSTRUCTION: Built to last with quality materials │
│                                                                 │
│  ═══════════════════════════════════════════════════════════   │
│  PRICE HISTORY TAB                                             │
│  ═══════════════════════════════════════════════════════════   │
│                                                                 │
│  [Toggle: ○ Price  ● Unit Price]  [Range: 30d 90d 1yr]        │
│                                                                 │
│       $30 ┤                                                    │
│           │      ╭────╮                                        │
│       $25 ┤──────╯    ╰────────────────────                   │
│           │                                                    │
│       $20 ┤                                                    │
│           └─────────────────────────────────────               │
│            Nov 1   Nov 15   Dec 1                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.8 Add Competitor Modal

```
┌────────────────────────────────────────────────────┐
│  Add Competitor                                    │
├────────────────────────────────────────────────────┤
│                                                    │
│  ASIN: [B0BKGXQBCB    ]                           │
│                                                    │
│  Pack Size: [2        ]  (units per listing)      │
│                                                    │
│  Marketplace: [Amazon.com (com) ▼]                │
│                                                    │
│  Schedule: [Weekly ▼]                             │
│    ○ Manual Only                                  │
│    ○ Daily                                        │
│    ○ Every 2 Days                                 │
│    ○ Every 3 Days                                 │
│    ● Weekly                                       │
│    ○ Custom: Every [__] days                     │
│                                                    │
│  Link to Keywords (optional):                     │
│    ☑ wf2 filter                                   │
│    ☐ kitchenaid filter                           │
│    ☑ refrigerator water filter                   │
│                                                    │
│  Notes: [_________________________________]       │
│                                                    │
│                    [Cancel]  [Add Competitor]     │
└────────────────────────────────────────────────────┘
```

### 8.9 Keywords Management Page

```
┌─────────────────────────────────────────────────────────────────┐
│  Keywords for HA-WF2-FLT                        [+ Add Keyword] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Keyword                  │ Channel SKUs │ Competitors│ [⋮] ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ wf2 filter               │     12       │     8      │ [⋮] ││
│  │ kitchenaid filter        │      5       │     6      │ [⋮] ││
│  │ refrigerator water filter│     23       │    15      │ [⋮] ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  Click keyword to manage Channel SKU and Competitor links       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.10 Link Channel SKUs Modal

```
┌────────────────────────────────────────────────────────────────┐
│  Link Channel SKUs to "wf2 filter"                             │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Search: [_______________]  [Select All] [Clear All]          │
│                                                                │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ ☑ HA-WF2-FLT-DL1      B0106TGBCA     Single              ││
│  │ ☑ HA-WF2-FLT-DL2      B0106TGBY8     Single              ││
│  │ ☑ HA-WF2-FLT-DL3      B00YU18HI2     Single              ││
│  │ ☐ HA-WF2-FLT-2PK-DL1  B0XXXXXXXX     2-Pack              ││
│  │ ☑ HA-WF2-FLT-2PK-DL2  B0YYYYYYYY     2-Pack              ││
│  │ ...                                                        ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                │
│  Or import from CSV: [Choose File]                            │
│                                                                │
│  Selected: 12 Channel SKUs                                    │
│                                                                │
│                              [Cancel]  [Save Links]           │
└────────────────────────────────────────────────────────────────┘
```

---

## 9. Future Considerations

### 9.1 AI Image Analysis (Next Phase)

- Integrate Claude/GPT to analyze competitor images
- Generate insights: main elements, quality indicators, improvement recommendations
- Compare to your listing images

### 9.2 Automated Competitor Discovery

- Use Amazon search results scraper
- Auto-find competitors for keywords
- Update competitor rankings based on search position

### 9.3 Advanced Analytics

- Sales/revenue estimation
- Keyword ranking tracking
- Share of voice analysis
- Market trend visualization

### 9.4 Price Changer Integration

- Direct API integration (not just export)
- Real-time price feeds
- Automated price adjustment triggers

### 9.5 Alerts & Notifications

- Email notifications for significant changes
- Slack/Teams integration
- Mobile push notifications
- Threshold-based alerting rules

### 9.6 Competitor Content Comparison

- Side-by-side title/bullet comparison
- Content gap analysis
- Keyword density comparison

---

## 10. Appendix

### 10.1 Marketplace Codes

| Code | Marketplace | URL Domain |
|------|-------------|------------|
| com | Amazon.com | amazon.com |
| ca | Amazon.ca | amazon.ca |
| co.uk | Amazon.co.uk | amazon.co.uk |
| de | Amazon.de | amazon.de |
| fr | Amazon.fr | amazon.fr |
| it | Amazon.it | amazon.it |
| es | Amazon.es | amazon.es |
| co.jp | Amazon.co.jp | amazon.co.jp |
| com.au | Amazon.com.au | amazon.com.au |
| com.mx | Amazon.com.mx | amazon.com.mx |

### 10.2 Schedule Options

| Schedule | Interval | Use Case |
|----------|----------|----------|
| manual | N/A | Low priority competitors |
| daily | 24 hours | High priority, price-sensitive |
| every_2_days | 48 hours | Important competitors |
| every_3_days | 72 hours | Standard monitoring |
| weekly | 7 days | Background monitoring |
| every_X_days | Custom | Flexible scheduling |

### 10.3 Sample Bulk Import CSV

**Competitors:**
```csv
asin,pack_size,schedule,notes
B0BKGXQBCB,2,weekly,Main competitor
B0D7VBZ3FM,1,daily,Price leader
B00K537MGC,1,weekly,Premium brand
```

**Keyword-Channel SKU Links:**
```csv
keyword,channel_sku
wf2 filter,HA-WF2-FLT-DL1
wf2 filter,HA-WF2-FLT-DL2
kitchenaid filter,HA-WF2-FLT-DL3
```

### 10.4 Data Retention Policy

| Data Type | Retention |
|-----------|-----------|
| Competitor current data | Forever (until deleted) |
| Price history | 1 year rolling |
| Scrape job logs | 90 days |
| Change alerts | 30 days |

### 10.5 Related PRDs

- **PRD_Amazon_Reviews_Scraper.md** - Core scraping infrastructure
- **PRD_Channel_SKU_Metrics.md** - Own listing metrics tracking

---

*— End of Document —*
