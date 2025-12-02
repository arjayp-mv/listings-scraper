# Product Requirements Document
## Amazon Reviews Scraper Tool

**Version:** 1.0  
**Date:** December 2024  
**Status:** Draft

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Project Overview](#2-project-overview)
3. [User Stories](#3-user-stories)
4. [Functional Requirements](#4-functional-requirements)
5. [Technical Architecture](#5-technical-architecture)
6. [Database Schema](#6-database-schema)
7. [API Endpoints](#7-api-endpoints)
8. [UI/UX Specifications](#8-uiux-specifications)
9. [Future Considerations](#9-future-considerations)
10. [Security & Configuration](#10-security--configuration)
11. [Appendix](#11-appendix)

---

## 1. Executive Summary

This document outlines the requirements for an internal Amazon Reviews Scraper tool. The tool will automate the collection of Amazon product reviews for competitor analysis, enabling the team to efficiently gather customer feedback data that informs product listing optimization.

### 1.1 Problem Statement

Currently, the team manually visits Amazon product pages for competitor listings, copies reviews into text files, and pastes them into AI tools (ChatGPT/Claude/Gemini) to generate product descriptions and bullet points. This process is time-consuming, error-prone, and doesn't scale well when analyzing multiple competitors.

### 1.2 Proposed Solution

A web-based application that automates Amazon review scraping using the Apify platform, with job queuing, SKU-based organization, and easy export capabilities. The tool will serve as a foundation for future enhancements including AI-powered copy generation.

### 1.3 Key Benefits

- Reduces manual data collection time by 90%+
- Ensures consistent, complete review data capture
- Organizes competitive intelligence by SKU for easy reference
- Enables team collaboration with shared access to scraped data
- Provides foundation for future AI integration

---

## 2. Project Overview

### 2.1 Scope

#### In Scope (Phase 1)

- Amazon reviews scraping via Apify
- SKU-based job organization
- Background job processing with queue
- Results viewing, filtering, and export
- Job history and re-run capabilities

#### Out of Scope (Future Phases)

- AI-powered description/bullet point generation
- Product details scraping
- Search results scraping
- User authentication

### 2.2 Technical Stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML5, CSS3, JavaScript (vanilla or jQuery) |
| Backend | Python (Flask or FastAPI) |
| Database | MySQL |
| External API | Apify (axesso_data/amazon-reviews-scraper actor) |
| Local Dev | XAMPP |
| Version Control | GitHub |

### 2.3 Users

- Multiple team members (no authentication required)
- Concurrent usage supported via job queue system

---

## 3. User Stories

### 3.1 Core Workflows

| ID | User Story | Acceptance Criteria |
|----|------------|---------------------|
| US-01 | As a user, I want to submit multiple ASINs for review scraping so I can analyze competitor products | • Can enter 1-30 ASINs in a text area<br>• Can associate job with a SKU<br>• Can name the job for easy reference<br>• Job is queued and processed in background |
| US-02 | As a user, I want to configure scraping options so I can get the reviews I need | • Can select marketplace (default: Amazon.com)<br>• Can choose star ratings (default: 4 and 5 star)<br>• Can set max pages (default: 10, max: 10)<br>• Can optionally filter by keyword |
| US-03 | As a user, I want to view and copy scraped reviews so I can use them in AI tools | • Reviews displayed as Title + Text format<br>• One-click copy button<br>• Reviews are deduplicated<br>• Empty results are excluded from output |
| US-04 | As a user, I want to export reviews in different formats | • Export to Excel (.xlsx)<br>• Export full JSON with metadata<br>• Copy formatted text to clipboard |
| US-05 | As a user, I want to see all jobs for a SKU so I can track competitive analysis | • View SKU list with associated jobs<br>• See job status, date, review count<br>• Access historical job results |
| US-06 | As a user, I want to manage job queue so I can control processing | • View queue status<br>• Cancel queued/running jobs<br>• Pause running jobs<br>• Retry failed ASINs |
| US-07 | As a user, I want warning when re-scraping ASINs so I avoid duplicates | • System detects previously scraped ASINs<br>• Option to merge new reviews with existing<br>• Option to create new job anyway |

---

## 4. Functional Requirements

### 4.1 Dashboard (Landing Page)

The dashboard provides an overview of system activity and quick access to key functions.

#### Components

1. **Active Jobs Panel:** Shows currently running and queued jobs with status indicators
2. **Recent Completed Jobs:** Lists last 10 completed jobs with quick-view links
3. **Quick Start Form:** Streamlined form to start a new scrape job
4. **Statistics Summary:** Total jobs, total reviews scraped, active SKUs

### 4.2 New Scrape Page

Primary interface for initiating review scraping jobs.

#### Input Fields

| Field | Type | Default | Required |
|-------|------|---------|----------|
| SKU | Text input with autocomplete | - | Yes |
| Job Name | Text input | - | Yes |
| ASINs | Textarea (one per line or comma-separated) | - | Yes |
| Marketplace | Dropdown | Amazon.com (com) | Yes |
| Sort By | Dropdown | Recent | Yes |
| Max Pages | Number input (1-10) | 10 | Yes |
| Star Ratings | Checkboxes (1-5 stars) | 4-star, 5-star checked | At least one |
| Keyword Filter | Text input | Empty (optional) | No |
| Reviewer Type | Dropdown | All Reviews | Yes |

#### Marketplace Options

| Domain Code | Marketplace | Region |
|-------------|-------------|--------|
| com | Amazon.com | USA |
| ca | Amazon.ca | Canada |
| co.uk | Amazon.co.uk | United Kingdom |
| de | Amazon.de | Germany |
| fr | Amazon.fr | France |
| it | Amazon.it | Italy |
| es | Amazon.es | Spain |
| co.jp | Amazon.co.jp | Japan |
| com.au | Amazon.com.au | Australia |
| com.mx | Amazon.com.mx | Mexico |
| in | Amazon.in | India |
| com.br | Amazon.com.br | Brazil |
| nl | Amazon.nl | Netherlands |
| se | Amazon.se | Sweden |
| ae | Amazon.ae | United Arab Emirates |

#### Validation & Duplicate Detection

- ASIN format validation (10 alphanumeric characters starting with B)
- Duplicate ASIN detection within same submission
- Warning if ASIN was previously scraped (shows last scrape date)
- Option to merge with existing data or create new job

### 4.3 Jobs Page

Central hub for viewing all scraping jobs and their status.

#### Job List View

- Sortable columns: Job Name, SKU, Status, Created Date, Review Count
- Filterable by: Status (All/Queued/Running/Completed/Failed), SKU, Date Range
- Pagination (20 jobs per page)
- Quick actions: View, Re-run, Delete

#### Job Status Indicators

| Status | Color | Description |
|--------|-------|-------------|
| Queued | Gray | Job submitted, waiting to be processed |
| Running | Blue (animated) | Job is currently being processed |
| Completed | Green | Job finished successfully |
| Partial | Yellow | Completed with some failed ASINs |
| Failed | Red | Job failed completely |
| Cancelled | Gray (strikethrough) | Job was cancelled by user |
| Paused | Orange | Job paused by user, can be resumed |

### 4.4 Job Detail Page

View and interact with results from a completed job. **This is where users get their output.**

#### Tabs/Views

1. **All Reviews:** Combined list of all reviews with search/filter
2. **By ASIN:** Reviews grouped by product (collapsible sections)
3. **By Star Rating:** Reviews grouped by 5-star, 4-star, etc.
4. **Failed ASINs:** List of ASINs that couldn't be scraped with retry option

#### Output Format

Reviews are displayed and copied in the following format:

```
[Review Title]
[Review Text]
```

**Example:**
```
Good humidifier filter
Good product good company. Works as expected.

Good value
Good filter that fit well. Exactly what I needed.
```

#### Export Options

- **Copy to Clipboard:** Copies all reviews in Title + Text format
- **Export Excel:** Downloads .xlsx with columns: ASIN, Title, Text, Rating, Date
- **Export JSON:** Full metadata export including all Apify response fields

#### Search & Filter

- Search box to find reviews containing specific keywords
- Filter by ASIN within job
- Filter by star rating

### 4.5 SKUs Page

Manage SKUs and view associated scraping jobs.

#### Features

- List all SKUs with job count and last activity date
- Click SKU to see all associated jobs
- Add notes/description to SKUs
- Delete SKU (with confirmation if jobs exist)
- Search SKUs

### 4.6 Settings Page

#### Configuration Options

- Apify API key management (stored in .env, displayed masked)
- Default scraping settings (can be overridden per job)
- Apify delay setting (seconds between API calls, default: 10)

#### Presets (Nice to Have)

- Save custom scraping presets (e.g., "Standard Analysis", "Quick Sample")
- Load preset when creating new job

---

## 5. Technical Architecture

### 5.1 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (HTML/JS)                      │
│  Dashboard │ New Scrape │ Jobs │ SKUs │ Settings            │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API
┌─────────────────────────┴───────────────────────────────────┐
│                  BACKEND (Python/FastAPI)                   │
│  API Routes │ Job Queue │ Apify Service │ Data Processing   │
└──────┬──────────────────────────────────────────┬───────────┘
       │                                          │
       ▼                                          ▼
┌──────────────────┐                    ┌─────────────────────┐
│     MySQL DB     │                    │     Apify API       │
│  Jobs, Reviews   │                    │  Reviews Scraper    │
└──────────────────┘                    └─────────────────────┘
```

### 5.2 Background Worker

Based on lessons from the integration guide, use a thread-based worker (NOT APScheduler).

- Worker polls for queued jobs every 30 seconds
- Processes one job at a time to avoid Apify memory limits
- Configurable delay between API calls (default: 10 seconds)
- Auto-recovery for stuck jobs
- Statistics synchronization to prevent counter drift

### 5.3 Apify Integration

**Actor:** `axesso_data~amazon-reviews-scraper`

> **Note:** Use tilde (`~`) not slash (`/`) in actor ID

#### Multiple Star Ratings Strategy

Since the Apify actor only accepts one star filter at a time, when user selects multiple star ratings (e.g., 4 and 5 star), the system will:

1. Create separate API calls for each star rating
2. Combine results after completion
3. Deduplicate reviews based on reviewId
4. Add delay between calls to respect rate limits

---

## 6. Database Schema

### 6.1 Tables Overview

#### skus

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT PK AUTO | Primary key |
| sku_code | VARCHAR(50) UNIQUE | SKU identifier (e.g., WF-UKF8001) |
| description | TEXT | Optional notes about the SKU |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

#### scrape_jobs

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT PK AUTO | Primary key |
| sku_id | BIGINT FK | Reference to skus table |
| job_name | VARCHAR(255) | User-provided job name |
| status | ENUM | queued, running, completed, partial, failed, cancelled, paused |
| marketplace | VARCHAR(10) | Domain code (com, ca, co.uk, etc.) |
| sort_by | VARCHAR(20) | recent or helpful |
| max_pages | INT | 1-10 |
| star_filters | JSON | ["five_star", "four_star"] |
| keyword_filter | VARCHAR(255) | Optional keyword filter |
| reviewer_type | VARCHAR(20) | all_reviews or verified_reviews |
| total_asins | INT | Number of ASINs in job |
| completed_asins | INT | Successfully processed |
| failed_asins | INT | Failed to process |
| total_reviews | INT | Unique reviews after dedup |
| apify_delay_seconds | INT DEFAULT 10 | Delay between API calls |
| error_message | TEXT | Error details if failed |
| created_at | TIMESTAMP | Job creation time |
| started_at | TIMESTAMP | Processing start time |
| completed_at | TIMESTAMP | Completion time |

#### job_asins

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT PK AUTO | Primary key |
| job_id | BIGINT FK | Reference to scrape_jobs |
| asin | VARCHAR(15) | Amazon ASIN |
| product_title | VARCHAR(500) | Product title from Amazon |
| status | ENUM | pending, running, completed, failed |
| reviews_found | INT | Number of reviews for this ASIN |
| apify_run_id | VARCHAR(50) | Apify run ID for tracking |
| error_message | TEXT | Error if failed |
| started_at | TIMESTAMP | Processing start |
| completed_at | TIMESTAMP | Processing end |

#### reviews

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT PK AUTO | Primary key |
| job_asin_id | BIGINT FK | Reference to job_asins |
| review_id | VARCHAR(50) UNIQUE | Amazon review ID (for dedup) |
| title | VARCHAR(500) | Review title |
| text | TEXT | Full review text |
| rating | VARCHAR(20) | Star rating string |
| date | VARCHAR(100) | Review date string |
| user_name | VARCHAR(200) | Reviewer name |
| verified | BOOLEAN | Verified purchase flag |
| helpful_count | INT | Number of helpful votes |
| raw_data | JSON | Full Apify response for this review |
| created_at | TIMESTAMP | Record creation time |

#### asin_history

Tracks all ASINs ever scraped for duplicate detection and merge functionality.

| Column | Type | Description |
|--------|------|-------------|
| id | BIGINT PK AUTO | Primary key |
| asin | VARCHAR(15) | Amazon ASIN |
| marketplace | VARCHAR(10) | Domain code |
| last_scraped_job_id | BIGINT FK | Most recent job that scraped this |
| last_scraped_at | TIMESTAMP | When it was last scraped |
| total_scrapes | INT | Number of times scraped |

### 6.2 Database Capacity Notes

MySQL can handle large text data effectively:

- TEXT type can store up to 65KB per review (more than enough for longest reviews)
- With proper indexing, querying millions of reviews is efficient
- JSON column for raw_data enables future analysis without schema changes
- Consider adding FULLTEXT index on title and text columns for search functionality

---

## 7. API Endpoints

### 7.1 Jobs API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/jobs | Create new scrape job |
| GET | /api/jobs | List all jobs (with pagination/filters) |
| GET | /api/jobs/{id} | Get job details |
| GET | /api/jobs/{id}/reviews | Get reviews for job (with filters) |
| GET | /api/jobs/{id}/export/excel | Export job reviews as Excel |
| GET | /api/jobs/{id}/export/json | Export full JSON with metadata |
| POST | /api/jobs/{id}/cancel | Cancel queued/running job |
| POST | /api/jobs/{id}/pause | Pause running job |
| POST | /api/jobs/{id}/resume | Resume paused job |
| POST | /api/jobs/{id}/retry-failed | Retry failed ASINs in job |
| DELETE | /api/jobs/{id} | Delete job and its data |

### 7.2 SKUs API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/skus | List all SKUs |
| POST | /api/skus | Create new SKU |
| GET | /api/skus/{id} | Get SKU details with jobs |
| PUT | /api/skus/{id} | Update SKU |
| DELETE | /api/skus/{id} | Delete SKU |
| GET | /api/skus/search?q={query} | Search SKUs (for autocomplete) |

### 7.3 Utility API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/dashboard/stats | Get dashboard statistics |
| POST | /api/asins/check-history | Check if ASINs were previously scraped |
| GET | /api/queue/status | Get current queue status |
| GET | /api/settings | Get current settings |
| PUT | /api/settings | Update settings |

---

## 8. UI/UX Specifications

### 8.1 Navigation

Top navigation bar with:

- Logo/App name (left)
- Nav links: Dashboard | New Scrape | Jobs | SKUs | Settings
- Queue status indicator (right) - shows number of queued/running jobs

### 8.2 Design Principles

- Clean, functional design prioritizing usability
- Responsive layout (works on desktop and tablet)
- Clear visual feedback for actions (loading states, success/error messages)
- Consistent color coding for job statuses
- Keyboard shortcuts for common actions (optional enhancement)

### 8.3 Key Interactions

#### New Scrape Form

- SKU field with autocomplete (creates new if not found)
- ASIN textarea validates format on blur
- Star rating checkboxes with "Select All" option
- Submit shows confirmation with estimated processing time
- Warning modal if duplicate ASINs detected

#### Job Results View

- Tab interface for different views (All, By ASIN, By Rating, Failed)
- Search box filters results in real-time
- "Copy All" button with visual confirmation
- Export dropdown (Excel, JSON)
- Long reviews shown in full (scrollable if needed)

---

## 9. Future Considerations

### 9.1 Phase 2: AI Copy Generation

- New tab/page for AI-powered description generation
- Select completed jobs as input data
- Configure AI parameters (tone, length, keywords to include)
- Generate bullet points and descriptions

### 9.2 Phase 3: Product Details Scraping

- Add product details scraper actor
- Scrape: title, description, bullet points, images, pricing
- Link to existing SKU/review data

### 9.3 Phase 4: Search Results Scraping

- Scrape Amazon search results for keywords
- Identify competitor ASINs automatically
- Track ranking positions over time

### 9.4 Extensibility Architecture

The database and code structure should support adding new Apify actors easily:

- Modular actor service classes
- Generic job queue supporting multiple job types
- Flexible database schema with JSON columns for actor-specific data
- Actor configuration stored in settings table

---

## 10. Security & Configuration

### 10.1 Environment Variables

All sensitive configuration stored in .env file (never committed to Git):

```env
# Apify Configuration
APIFY_API_KEY=your_api_key_here

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=amazon_reviews_scraper
```

### 10.2 .gitignore Requirements

```
.env
*.pyc
__pycache__/
venv/
node_modules/
```

---

## 11. Appendix

### 11.1 Apify Actor Reference

**Actor ID:** `axesso_data~amazon-reviews-scraper`  
**Documentation:** https://apify.com/axesso_data/amazon-reviews-scraper

### 11.2 Sample Apify Input

```json
{
  "input": [{
    "asin": "B01LWAPPVI",
    "domainCode": "com",
    "sortBy": "recent",
    "maxPages": 10,
    "filterByStar": "five_star",
    "reviewerType": "all_reviews",
    "formatType": "current_format",
    "mediaType": "all_contents"
  }]
}
```

### 11.3 Sample Output Format (for copy/paste)

```
Good humidifier filter
Good product good company.

Good value
Good filter that fit well

Good product
As advertised

The filter does a good job with our humidifier.
The filters work well in the humidifier. We also have hard water so this filter we works with our hard water. Very easy to swap out.
```

### 11.4 Key Lessons from Integration Guide

- Use thread-based worker, NOT APScheduler (fails with uvicorn reload)
- Add configurable delay between Apify calls (10-30 seconds) to avoid memory limits
- Use tilde (`~`) not slash (`/`) in actor IDs
- Commit data BEFORE metadata to prevent data loss
- Sync statistics every tick to prevent counter drift
- Auto-detect stuck rows (RUNNING status with no apify_run_id > 10 min)
- Store error messages for debugging and user visibility

### 11.5 SKU Examples

Based on your format:
- `WF-UKF8001`
- `HA-WF2-FLT`
- `UB-YTX14-BS`

---

*— End of Document —*
