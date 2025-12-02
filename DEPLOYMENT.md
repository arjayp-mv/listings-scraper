# Deployment Guide - Amazon Reviews Scraper

## What You'll Receive
1. **GitHub Repository**: https://github.com/arjayp-mv/listings-scraper
2. **Database Export**: SQL file exported from phpMyAdmin (includes schema + data)
3. **Apify API Key**: (provided separately by Arjay)

---

## Server Requirements

| Requirement | Version | Notes |
|------------|---------|-------|
| Python | 3.10+ | Required |
| MySQL | 5.7+ or 8.0 | MariaDB also works |
| OS | Linux (Ubuntu recommended) or Windows Server | |
| RAM | 2GB minimum | |
| Port | 8080 (configurable) | Must be open for web access |

---

## Step 1: Clone Repository

```bash
git clone https://github.com/arjayp-mv/listings-scraper.git
cd listings-scraper
```

---

## Step 2: Import Database

**Option A - Command Line:**
```bash
# Create database and import the SQL file
mysql -u <username> -p -e "CREATE DATABASE IF NOT EXISTS amazon_reviews_scraper;"
mysql -u <username> -p amazon_reviews_scraper < database_export.sql
```

**Option B - phpMyAdmin:**
1. Create database named `amazon_reviews_scraper`
2. Import the SQL file provided

---

## Step 3: Setup Python Environment

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Python Dependencies (all documented in requirements.txt)

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.109.2 | Web framework |
| uvicorn[standard] | 0.27.1 | ASGI server |
| sqlalchemy | 2.0.25 | Database ORM |
| pymysql | 1.1.0 | MySQL driver |
| apify-client | 1.6.4 | Apify API integration |
| pydantic | 2.6.1 | Data validation |
| pydantic-settings | 2.1.0 | Environment config |
| python-dotenv | 1.0.1 | .env file loading |
| openpyxl | 3.1.2 | Excel export |
| httpx | 0.26.0 | HTTP client |
| python-multipart | 0.0.9 | Form data handling |

---

## Step 4: Configure Environment

Create `.env` file in `backend/` folder (copy from `.env.example`):

```env
# Server Configuration
HOST=0.0.0.0
PORT=8080

# Apify Configuration (GET API KEY FROM ARJAY)
APIFY_API_KEY=apify_api_xxxxxxxxxxxxxxxxxxxxxxx

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=amazon_reviews_scraper

# Worker Configuration
WORKER_INTERVAL_SECONDS=30
APIFY_DELAY_SECONDS=10
```

> **IMPORTANT**: Never commit `.env` to version control. It contains sensitive credentials.

---

## Step 5: Run the Server

### Development/Testing

```bash
cd backend
uvicorn src.main:app --host 0.0.0.0 --port 8080
```

### Production (Linux with systemd)

Create service file `/etc/systemd/system/amazon-scraper.service`:

```ini
[Unit]
Description=Amazon Reviews Scraper
After=network.target mysql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/listings-scraper/backend
Environment="PATH=/path/to/listings-scraper/backend/venv/bin"
ExecStart=/path/to/listings-scraper/backend/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable amazon-scraper
sudo systemctl start amazon-scraper
sudo systemctl status amazon-scraper
```

View logs:
```bash
sudo journalctl -u amazon-scraper -f
```

---

## Step 6: Configure Reverse Proxy (Optional but Recommended)

### Nginx Configuration

Create `/etc/nginx/sites-available/amazon-scraper`:

```nginx
server {
    listen 80;
    server_name scraper.yourcompany.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/amazon-scraper /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Step 7: Verify Installation

1. Open browser to `http://server-ip:8080`
2. Dashboard should load with dark theme
3. Try creating a test scrape job via Product Reviews > New Scrape
4. API documentation available at `http://server-ip:8080/docs`

---

## Application Features

### 1. Product Reviews (Review Scraping)

Scrape Amazon reviews for analysis. Reviews are formatted as "Title + Text" for copying into AI tools.

**Navigation:** Product Reviews dropdown
- **New Scrape**: Create a scrape job with ASINs and star filters
- **Jobs**: View all scrape jobs and their status
- **SKU Reviews**: Organize reviews by product SKU

**Workflow:**
1. Go to New Scrape, enter ASINs and select star filters
2. Job queues and background worker processes it
3. View results in job detail page
4. Copy formatted reviews or export to Excel

### 2. Channel SKU Metrics (Product Tracking)

Track product ratings/review counts over time across multiple Amazon marketplaces.

**Navigation:** Channel SKU Metrics dropdown
- **New Scan**: Start a scan job for your tracked listings
- **Scan History**: View past scan jobs and results
- **All Listings**: Manage all tracked Channel SKUs
- **Parent SKUs**: View metrics aggregated by parent SKU

**Workflow:**
1. Import Channel SKUs via CSV (All Listings > Import CSV)
2. Run a scan job (New Scan)
3. View results to track rating/review changes over time

---

## Project Structure

```
listings-scraper/
├── backend/
│   ├── src/
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── config.py        # Environment configuration
│   │   ├── database.py      # SQLAlchemy setup
│   │   ├── pagination.py    # Pagination utilities
│   │   ├── jobs/            # Scrape jobs domain (models, router, service)
│   │   ├── skus/            # SKUs domain (for review scraping)
│   │   ├── reviews/         # Reviews domain
│   │   ├── channel_skus/    # Channel SKU domain (product metrics tracking)
│   │   ├── product_scans/   # Product scan jobs domain
│   │   ├── apify/           # Apify API integration
│   │   └── workers/         # Background scraper worker
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Environment config (CREATE THIS)
├── frontend/
│   ├── index.html           # Dashboard
│   ├── new-scrape.html      # New review scrape form
│   ├── jobs.html            # Review scrape jobs list
│   ├── job-detail.html      # Job detail with copy/export
│   ├── skus.html            # SKU management (for reviews)
│   ├── sku-reviews.html     # Reviews for a specific SKU
│   ├── new-scan.html        # New product metrics scan
│   ├── scans.html           # Product scan history
│   ├── scan-detail.html     # Scan detail view
│   ├── listings.html        # All Channel SKU listings
│   ├── skus-list.html       # Parent SKUs overview
│   ├── sku-detail.html      # Channel SKUs for a parent SKU
│   ├── css/styles.css       # Dark theme styles
│   └── js/
│       ├── nav.js           # Shared navigation component
│       ├── api.js           # API utilities
│       └── *.js             # Page-specific JavaScript
├── database_setup.sql       # Database schema (use export for data)
├── .env.example             # Template for .env file
├── README.md                # General documentation
└── DEPLOYMENT.md            # This file
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Port already in use | Change `PORT` in `.env` to another port (e.g., 8081) |
| Database connection failed | Check DB credentials in `.env`, ensure MySQL is running |
| `ModuleNotFoundError` | Ensure virtual environment is activated and `pip install -r requirements.txt` was run |
| Apify errors | Verify API key is correct, check Apify account has credits |
| Static files not loading | Ensure `frontend/` folder exists in project root |
| 500 Internal Server Error | Check server logs: `journalctl -u amazon-scraper -f` |

---

## Background Worker

The application includes a background worker that:
- Runs every 30 seconds (configurable via `WORKER_INTERVAL_SECONDS`)
- Picks up queued scrape jobs and processes them
- Calls Apify API to scrape Amazon reviews
- Automatically starts when the server starts

No additional cron jobs or schedulers needed.

---

## API Endpoints Reference

### Product Reviews (Scraping)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/jobs` | POST | Create new scrape job |
| `/api/jobs` | GET | List jobs (paginated) |
| `/api/jobs/{id}` | GET | Get job details |
| `/api/jobs/{id}` | DELETE | Delete job and reviews |
| `/api/jobs/{id}/cancel` | POST | Cancel running job |
| `/api/jobs/{id}/reviews/formatted` | GET | Get reviews as text |
| `/api/jobs/{id}/reviews/export/excel` | GET | Download Excel file |
| `/api/skus` | GET | List SKUs |
| `/api/skus` | POST | Create SKU |
| `/api/skus/search` | GET | Search SKUs by code |
| `/api/skus/{id}/reviews` | GET | Get reviews for a SKU |

### Channel SKU Metrics (Product Tracking)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/channel-skus` | GET | List all channel SKUs |
| `/api/channel-skus` | POST | Create channel SKU |
| `/api/channel-skus/import` | POST | Bulk import from CSV |
| `/api/channel-skus/export` | GET | Export to CSV |
| `/api/channel-skus/{id}` | GET | Get channel SKU details |
| `/api/channel-skus/{id}` | PUT | Update channel SKU |
| `/api/channel-skus/{id}` | DELETE | Delete channel SKU |
| `/api/product-scans` | POST | Create product scan job |
| `/api/product-scans` | GET | List scan jobs |
| `/api/product-scans/{id}` | GET | Get scan details |
| `/api/product-scans/{id}/cancel` | POST | Cancel running scan |

### Dashboard

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard/stats` | GET | Dashboard statistics |
| `/docs` | GET | Interactive API documentation |

---

## Contact

- **Apify API Key**: Request from Arjay
- **Database Issues**: Ensure SQL export was imported completely
- **Python Errors**: Verify Python 3.10+ and all requirements installed
