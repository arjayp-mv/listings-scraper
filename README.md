# Amazon Reviews Scraper

A web application to automate Amazon review scraping using the Apify platform. Built with Python/FastAPI backend, MySQL database, and HTML/JavaScript frontend.

## Features

- **Scrape Amazon Reviews**: Enter ASINs and automatically scrape reviews from Amazon
- **Multiple Star Filters**: Select any combination of star ratings to scrape
- **Background Processing**: Jobs run in background with real-time status updates
- **Copy Reviews**: One-click copy of formatted reviews (Title + Text) for AI tools
- **Export Options**: Download reviews as Excel or JSON
- **SKU Organization**: Organize scrape jobs by product SKUs
- **ASIN History**: Warns when ASINs have been scraped before

## Requirements

- Python 3.10+
- XAMPP (MySQL)
- Apify account with API key

## Quick Start

### 1. Database Setup

1. Start XAMPP and ensure MySQL is running
2. Open phpMyAdmin (http://localhost/phpmyadmin)
3. Run the SQL in `database_setup.sql` to create the database and tables

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

The `.env` file is already configured. Update if needed:

```env
HOST=0.0.0.0
PORT=8080
APIFY_API_KEY=your_apify_api_key
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=amazon_reviews_scraper
```

### 4. Run the Server

```bash
cd backend
python -m src.main
```

Or with uvicorn directly:

```bash
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

### 5. Access the Application

Open http://localhost:8080 in your browser.

## Usage

### Creating a New Scrape Job

1. Click "New Scrape" in the navigation
2. Enter a job name and optionally select/create a SKU
3. Paste ASINs (one per line or comma-separated)
4. Configure scraping options:
   - **Marketplace**: Amazon domain (default: .com)
   - **Sort By**: Most Recent or Most Helpful
   - **Max Pages**: 1-20 pages per ASIN
   - **Star Filters**: Select which star ratings to scrape
   - **Keyword Filter**: Optional keyword filter
   - **Reviewer Type**: All reviews or verified only
5. Click "Start Scraping"

### Copying Reviews

1. Go to the Job Detail page
2. Click "Copy All Reviews" to copy formatted text
3. Paste into ChatGPT, Claude, or other AI tools

### Exporting Data

- **Excel**: Click "Download Excel" for a spreadsheet
- **JSON**: Click "Download JSON" for raw data

## Project Structure

```
amazon-reviews-scraper/
├── backend/
│   ├── src/
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── config.py        # Environment configuration
│   │   ├── database.py      # SQLAlchemy setup
│   │   ├── pagination.py    # Pagination utilities
│   │   ├── jobs/            # Jobs domain
│   │   ├── skus/            # SKUs domain
│   │   ├── reviews/         # Reviews domain
│   │   ├── apify/           # Apify integration
│   │   └── workers/         # Background worker
│   └── requirements.txt
├── frontend/
│   ├── index.html           # Dashboard
│   ├── new-scrape.html      # New scrape form
│   ├── jobs.html            # Jobs list
│   ├── job-detail.html      # Job detail with copy
│   ├── skus.html            # SKU management
│   ├── css/styles.css       # Styles
│   └── js/                  # JavaScript files
├── database_setup.sql       # MySQL schema
├── .env                     # Environment config
└── README.md
```

## API Endpoints

### Jobs
- `POST /api/jobs` - Create new scrape job
- `GET /api/jobs` - List jobs (with pagination)
- `GET /api/jobs/{id}` - Get job details
- `POST /api/jobs/{id}/cancel` - Cancel job
- `POST /api/jobs/{id}/retry-failed` - Retry failed ASINs
- `DELETE /api/jobs/{id}` - Delete job

### Reviews
- `GET /api/jobs/{id}/reviews` - List reviews
- `GET /api/jobs/{id}/reviews/formatted` - Get formatted text
- `GET /api/jobs/{id}/reviews/stats` - Get statistics
- `GET /api/jobs/{id}/reviews/export/excel` - Export Excel
- `GET /api/jobs/{id}/reviews/export/json` - Export JSON

### SKUs
- `GET /api/skus` - List SKUs
- `POST /api/skus` - Create SKU
- `GET /api/skus/{id}` - Get SKU
- `PUT /api/skus/{id}` - Update SKU
- `DELETE /api/skus/{id}` - Delete SKU
- `GET /api/skus/search` - Search SKUs

### Utility
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/queue/status` - Queue status
- `POST /api/jobs/check-history` - Check ASIN history

## Troubleshooting

### Port already in use
Change `PORT` in `.env` to a different port (e.g., 8081)

### Database connection failed
1. Ensure XAMPP MySQL is running
2. Verify database credentials in `.env`
3. Make sure `amazon_reviews_scraper` database exists

### Apify errors
1. Verify your API key is correct in `.env`
2. Check your Apify account has sufficient credits
3. Some ASINs may not have reviews available
