# XAMPP & MySQL Guide for Windows

## Purpose
This guide teaches Claude Code instances how to properly work with XAMPP MySQL on Windows. It covers database creation, running SQL scripts, and common pitfalls.

---

## Table of Contents
1. [Critical Rules - DO NOT Run SQL via Bash](#1-critical-rules---do-not-run-sql-via-bash)
2. [How This Project Handles Database](#2-how-this-project-handles-database)
3. [XAMPP MySQL Access Methods](#3-xampp-mysql-access-methods)
4. [Database Configuration](#4-database-configuration)
5. [Running Migration Scripts](#5-running-migration-scripts)
6. [Common Database Operations](#6-common-database-operations)
7. [Troubleshooting](#7-troubleshooting)
8. [Quick Reference](#8-quick-reference)

---

## 1. Critical Rules - DO NOT Run SQL via Bash

### NEVER Do This
```bash
# WRONG - These will fail or cause issues
mysql -u root -p < migrations/001_initial_schema.sql
mysql -e "CREATE DATABASE listings_workflow"
sqlite3 database.db < schema.sql
psql -c "CREATE TABLE..."
```

### Why This Fails on XAMPP Windows
1. **MySQL CLI not in PATH** - XAMPP doesn't add mysql.exe to system PATH
2. **Password prompts** - Interactive password prompts break automation
3. **Path issues** - Windows paths with backslashes cause problems
4. **Encoding issues** - PowerShell may corrupt SQL file encoding

### What To Do Instead
This project uses **SQLAlchemy auto-migration** - the database tables are created automatically when the server starts. You do NOT need to run SQL files manually.

---

## 2. How This Project Handles Database

### Automatic Table Creation
When the FastAPI server starts, it automatically creates all tables:

```python
# main.py - startup event
@app.on_event("startup")
async def startup_event():
    init_db()  # This creates all tables automatically
    logger.info("Database initialized successfully")
```

```python
# config/database.py
def init_db():
    """Creates all tables defined in models."""
    from src.models import projects, subprojects, keywords, scraping_jobs, scraping_rows, pipeline_columns
    Base.metadata.create_all(bind=engine)
```

### What You Need to Do
1. **Create the database manually** (one-time setup via phpMyAdmin)
2. **Start the server** - Tables are created automatically
3. **Run migration scripts** (only for schema changes) - Via phpMyAdmin

### The Database Must Exist First
SQLAlchemy can create tables, but it CANNOT create the database itself. The database `listings_workflow` must exist before starting the server.

---

## 3. XAMPP MySQL Access Methods

### Method 1: phpMyAdmin (RECOMMENDED)
This is the safest and easiest way to manage MySQL on XAMPP.

**Access URL:** http://localhost/phpmyadmin

**Steps to Create Database:**
1. Open http://localhost/phpmyadmin in browser
2. Click "New" in the left sidebar
3. Enter database name: `listings_workflow`
4. Select collation: `utf8mb4_unicode_ci`
5. Click "Create"

**Steps to Run SQL Scripts:**
1. Open http://localhost/phpmyadmin
2. Select the `listings_workflow` database
3. Click "SQL" tab at the top
4. Copy/paste SQL content from migration file
5. Click "Go" to execute

### Method 2: MySQL CLI (If Configured)
Only works if you've added XAMPP MySQL to PATH.

**Add to PATH (one-time setup):**
```
C:\xampp\mysql\bin
```

**Then you can use:**
```powershell
cd C:\xampp\mysql\bin
.\mysql.exe -u root -e "CREATE DATABASE listings_workflow"
```

### Method 3: HeidiSQL / MySQL Workbench
Third-party GUI tools that connect to XAMPP MySQL.

**Connection Settings:**
- Host: localhost
- Port: 3306
- User: root
- Password: (empty by default)

---

## 4. Database Configuration

### Environment Variables (.env file)
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=listings_workflow

# Apify Configuration
APIFY_API_KEY=your_api_key_here

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8004
DEBUG=True
```

### Default XAMPP MySQL Settings
| Setting | Value |
|---------|-------|
| Host | localhost |
| Port | 3306 |
| Username | root |
| Password | (empty) |
| Socket | N/A (Windows uses TCP) |

### Connection String Format
```
mysql+mysqlconnector://root:@localhost:3306/listings_workflow
```

---

## 5. Running Migration Scripts

### Migration Files Location
```
migrations/
  001_initial_schema.sql      # Creates all tables
  002_fix_enum_columns.sql    # Fixes ENUM to VARCHAR
  003_add_archived_at.sql     # Adds archiving feature
  004_add_apify_delay.sql     # Adds rate limiting
  005_add_saved_filters.sql   # Adds saved filters
  006_add_processing_status.sql # Adds workflow status
```

### When to Run Migrations
- **001_initial_schema.sql** - Only if tables don't exist AND you want views/indexes
- **002-006** - Only when adding new features that need schema changes

### How to Run Migrations (via phpMyAdmin)

#### Step 1: Open phpMyAdmin
Navigate to: http://localhost/phpmyadmin

#### Step 2: Select Database
Click on `listings_workflow` in the left sidebar

#### Step 3: Open SQL Tab
Click the "SQL" tab at the top of the page

#### Step 4: Copy Migration Content
Read the migration file and copy its content:
```sql
-- Example: contents of 003_add_archived_at.sql
ALTER TABLE scraping_jobs
ADD COLUMN archived_at TIMESTAMP NULL
COMMENT 'NULL = active, NOT NULL = archived';

CREATE INDEX idx_archived_at ON scraping_jobs(archived_at);
```

#### Step 5: Execute
Paste into phpMyAdmin SQL box and click "Go"

### Migration Best Practices
1. **Always backup first** - Export database before running migrations
2. **Run in order** - Migrations depend on previous ones
3. **Check for errors** - phpMyAdmin shows errors in red
4. **One at a time** - Don't run multiple migrations together

---

## 6. Common Database Operations

### Check if Database Exists
**Via phpMyAdmin:**
1. Look in left sidebar for `listings_workflow`
2. If not there, create it

**Via Python (in code):**
```python
from config.database import engine
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Database connection successful")
except Exception as e:
    print(f"Database error: {e}")
```

### Check if Tables Exist
**Via phpMyAdmin:**
1. Click on `listings_workflow`
2. Look for tables: projects, subprojects, keywords, etc.

**Via Server Startup:**
Just start the server - it will create missing tables:
```powershell
cd C:\Users\Arjay\Downloads\listings-workflow
python main.py
```

### View Table Structure
**Via phpMyAdmin:**
1. Click on table name (e.g., `projects`)
2. Click "Structure" tab
3. See all columns, types, indexes

### Export Database
**Via phpMyAdmin:**
1. Select `listings_workflow` database
2. Click "Export" tab
3. Choose "Quick" or "Custom"
4. Click "Go" to download .sql file

### Import Database
**Via phpMyAdmin:**
1. Create empty database first
2. Select the database
3. Click "Import" tab
4. Choose .sql file
5. Click "Go"

---

## 7. Troubleshooting

### Error: "Unknown database 'listings_workflow'"
**Cause:** Database doesn't exist
**Fix:** Create it via phpMyAdmin:
1. Open http://localhost/phpmyadmin
2. Click "New"
3. Name: `listings_workflow`
4. Collation: `utf8mb4_unicode_ci`
5. Click "Create"

### Error: "Can't connect to MySQL server"
**Cause:** XAMPP MySQL not running
**Fix:**
1. Open XAMPP Control Panel
2. Click "Start" next to MySQL
3. Wait for it to turn green
4. Verify: http://localhost/phpmyadmin should load

### Error: "Access denied for user 'root'@'localhost'"
**Cause:** Password mismatch
**Fix:**
1. Check if XAMPP MySQL has a password set
2. Update `.env` file with correct password:
   ```env
   DB_PASSWORD=your_password
   ```
3. Or reset MySQL password via phpMyAdmin

### Error: "Table already exists"
**Cause:** Running migration twice
**Fix:**
- Safe to ignore if table structure is correct
- Or use `CREATE TABLE IF NOT EXISTS` (migrations already do this)

### Error: "mysql is not recognized"
**Cause:** Trying to run mysql CLI without it being in PATH
**Fix:** Don't use CLI - use phpMyAdmin instead, or add to PATH:
```
C:\xampp\mysql\bin
```

### Error: "XAMPP MySQL port 3306 in use"
**Cause:** Another MySQL instance running
**Fix:**
```powershell
# Find what's using port 3306
netstat -ano | findstr ":3306"

# Stop the conflicting process
Stop-Process -Id [PID] -Force
```

### Error: "SQLAlchemy can't connect"
**Cause:** Various connection issues
**Checklist:**
1. Is XAMPP MySQL running? (Check XAMPP Control Panel)
2. Is the database created? (Check phpMyAdmin)
3. Is `.env` file correct? (Check DB_HOST, DB_PORT, DB_USER, DB_PASSWORD)
4. Is the port blocked by firewall?

---

## 8. Quick Reference

### XAMPP Control Panel Location
```
C:\xampp\xampp-control.exe
```

### phpMyAdmin URL
```
http://localhost/phpmyadmin
```

### Database Connection Details
```
Host:     localhost
Port:     3306
User:     root
Password: (empty)
Database: listings_workflow
```

### Project Database Tables
| Table | Purpose |
|-------|---------|
| projects | Main projects (one per SKU) |
| subprojects | Variations under projects |
| keywords | Keywords for each subproject |
| scraping_jobs | Job metadata and progress |
| scraping_rows | Individual CSV rows being processed |
| pipeline_columns | Column visibility settings |

### Verify XAMPP MySQL is Running
```powershell
netstat -ano | findstr ":3306"
```
Should show a LISTENING process.

### Start Server (Creates Tables Automatically)
```powershell
cd C:\Users\Arjay\Downloads\listings-workflow
python main.py
```

### Check Tables Were Created
After starting server, check phpMyAdmin - all 6 tables should exist.

---

## Summary: Database Setup Workflow

### First-Time Setup
1. **Start XAMPP** - Open XAMPP Control Panel, start Apache and MySQL
2. **Create Database** - Via phpMyAdmin, create `listings_workflow`
3. **Configure .env** - Ensure database credentials are correct
4. **Start Server** - `python main.py` - Tables created automatically

### Adding New Features (Schema Changes)
1. **Create Migration File** - `migrations/007_new_feature.sql`
2. **Run via phpMyAdmin** - Copy/paste SQL, click Go
3. **Update Models** - Add new columns to SQLAlchemy models
4. **Restart Server** - New model changes take effect

### Key Takeaways
1. **Never run SQL via Bash** on Windows/XAMPP
2. **Use phpMyAdmin** for all database operations
3. **Tables auto-create** when server starts (via SQLAlchemy)
4. **Database must exist first** - Create manually via phpMyAdmin
5. **Migrations are optional** - Only for views, indexes, or complex changes
