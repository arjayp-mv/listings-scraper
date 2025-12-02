# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Amazon Reviews Scraper - A web application for scraping Amazon product reviews using Apify's `axesso_data~amazon-reviews-scraper` actor. Reviews are formatted as "Title + Text" for easy copying into AI tools (ChatGPT, Claude, Gemini).

## Common Commands

```bash
# Setup (from project root)
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Database setup (run in phpMyAdmin)
# Execute database_setup.sql to create schema

# Run server - see "Starting the Server on Windows" section below
```

## Starting the Server on Windows

**IMPORTANT**: Use `reload=False` to avoid WinError 10013 on Windows.

### Step 1: Kill Existing Server on Port 9000
**IMPORTANT**: Don't use `taskkill /F /IM python.exe` - it kills ALL Python processes including other servers!

Instead, kill only the server on port 9000:
```bash
# Find PID using port 9000
netstat -ano | findstr ":9000"
# Output shows: TCP 0.0.0.0:9000 ... LISTENING <PID>

# Kill that specific PID (use // in Git Bash, / gets interpreted as path)
taskkill //F //PID <pid_number>
```

Or use the `KillShell` tool with the shell_id from a running background Bash task (preferred).

### Step 2: Start Server in Background
**MUST use `run_in_background: true`** in the Bash tool:
```bash
cd "C:\Users\Arjay\Downloads\Amazon Reviews Scraper\backend" && python -c "import uvicorn; uvicorn.run('src.main:app', host='0.0.0.0', port=9000, reload=False)"
```

### Step 3: Check Server Output
Use `BashOutput` tool with the shell_id to verify server started successfully. Look for:
```
INFO:     Uvicorn running on http://0.0.0.0:9000 (Press CTRL+C to quit)
```

### Port Conflicts
- Port 8080 is often used by XAMPP Apache
- Use port 9000 or another high port to avoid conflicts
- Check port: `netstat -ano | findstr ":9000"`

### Stop Server Methods
1. **KillShell tool** (preferred): Use `KillShell` with the background shell_id
2. **By PID** (recommended): Find PID with `netstat -ano | findstr ":9000"`, then `taskkill //F //PID <pid>`
3. **AVOID**: `taskkill //F //IM python.exe` - kills ALL Python processes including other servers!

## Playwright MCP Testing

### Available Tools
| Tool | Purpose |
|------|---------|
| `mcp__playwright__browser_navigate` | Navigate to URL |
| `mcp__playwright__browser_snapshot` | Get page accessibility tree (PREFERRED for finding elements) |
| `mcp__playwright__browser_click` | Click elements using `ref` from snapshot |
| `mcp__playwright__browser_type` | Type text into inputs |
| `mcp__playwright__browser_fill_form` | Fill multiple form fields at once |
| `mcp__playwright__browser_wait_for` | Wait for text/element/time |
| `mcp__playwright__browser_take_screenshot` | Take screenshot (use for visual verification) |
| `mcp__playwright__browser_close` | Close browser session |

### Complete Testing Workflow

**Before Testing:**
1. Kill existing Python processes: `taskkill /F /IM python.exe`
2. Start server with `run_in_background: true`
3. Verify server started via `BashOutput`

**Testing Steps:**
1. `browser_navigate` to `http://localhost:9000`
2. `browser_snapshot` to get page structure and element refs
3. Interact using `ref` values from snapshot:
   - `browser_click` for buttons/links
   - `browser_type` for text inputs (use `submit: true` to press Enter)
   - `browser_fill_form` for multiple fields
4. Take fresh `browser_snapshot` after each page change
5. `browser_take_screenshot` for visual documentation
6. `browser_close` when done

### Key Rules
- **Always snapshot first** - Get fresh `ref` values before clicking/typing
- **Refs change after page updates** - Take new snapshot after navigation or actions
- **Use `submit: true`** in `browser_type` to trigger form submission
- **Verify database** - After database operations, query the database directly

### Application URLs
| Page | URL |
|------|-----|
| Dashboard | `http://localhost:9000` |
| New Scrape Job | `http://localhost:9000/new-scrape.html` |
| Job Detail | `http://localhost:9000/job-detail.html?id={job_id}` |
| Jobs List | `http://localhost:9000/jobs.html` |
| SKU Management | `http://localhost:9000/skus.html` |

### Test Data (from docs/test.md)
- SKU: `HA-MAF1-FLT`
- ASINs: `B0893V5PYC`, `B0BG2J4NJ1`
- Max Pages: 3

## Architecture

### Domain-Based Structure
The backend uses Netflix's Dispatch-inspired domain structure where each feature domain has its own folder with all related files:

```
backend/src/
├── jobs/       # Scrape job management (models, schemas, service, router, dependencies)
├── skus/       # Product SKU organization
├── reviews/    # Review storage and formatting
├── apify/      # External Apify API integration (client, schemas, exceptions)
├── workers/    # Background job processing (thread-based, not APScheduler)
├── config.py   # Global settings via pydantic-settings
├── database.py # SQLAlchemy engine and session
├── pagination.py # Reusable pagination utilities
└── main.py     # FastAPI app entry point
```

### Key Patterns

**Background Processing**: Uses thread-based worker (not APScheduler) for uvicorn --reload compatibility. Worker runs in `workers/scraper_worker.py` with immediate tick on startup then every 30 seconds.

**Multiple Star Filters**: Apify actor only accepts one star filter per call. Solution: make separate API calls for each selected star rating, then deduplicate results by `reviewId`.

**Apify Actor ID Format**: Use tilde `~` not slash `/` (e.g., `axesso_data~amazon-reviews-scraper`).

**Database Aggregation**: Use SQLAlchemy `func.count()` and `func.sum()` with `.group_by()` instead of Python loops for counting/aggregating.

### Data Flow
1. User submits job via frontend form → `POST /api/jobs` creates job + job_asins records
2. Background worker picks up queued jobs → calls Apify for each ASIN × star filter combination
3. Reviews deduplicated by `reviewId` and stored in `review` table
4. User views job detail → `GET /api/jobs/{id}/reviews/formatted` returns Title + Text format
5. One-click copy button copies formatted text to clipboard

### Database Tables
- `sku` - Product SKU groupings (optional job organization)
- `scrape_job` - Job config and progress stats
- `job_asin` - Individual ASINs within a job with status
- `review` - Scraped reviews with raw_data JSON
- `asin_history` - Track previously scraped ASINs to warn duplicates

## Code Standards

**File Size Limits**:
- Optimal: 200-300 lines
- Acceptable: 300-400 lines
- Maximum: 500 lines (split immediately)

**Pagination**: All list endpoints return max 50 items. Use `pagination.py` utilities.

**Service Layer Pattern**: Each domain has a service class containing business logic. Routers are thin and delegate to services.

**Dependencies Pattern**: Use FastAPI's `Depends()` for validation (e.g., `valid_job` in `jobs/dependencies.py` validates job exists and raises 404).

**Response Models**: All endpoints use Pydantic `response_model` for type safety.

## Environment Configuration

Configuration via `.env` file loaded by `pydantic-settings`:
- `APIFY_API_KEY` - Required for Apify API calls
- `DB_*` - MySQL connection (default: XAMPP localhost:3306)
- `PORT` - Server port (default: 8080)
- `WORKER_INTERVAL_SECONDS` - Background worker interval (default: 30)
