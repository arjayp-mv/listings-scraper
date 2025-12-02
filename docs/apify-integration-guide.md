# Apify Integration Documentation for New Applications

## Overview

This documentation provides comprehensive guidance for integrating Apify API into Python/FastAPI applications. It is based on production-tested patterns from a listings workflow application that processes thousands of scraping jobs using the Amazon autocomplete actor.

**Target Audience:** Developers building new applications with Apify integration
**Source Codebase:** listings-workflow (Python/FastAPI/SQLAlchemy)

---

## Table of Contents

1. [Initial Setup & Configuration](#1-initial-setup--configuration)
2. [Apify Client Implementation](#2-apify-client-implementation)
3. [Background Worker Architecture](#3-background-worker-architecture)
4. [Rate Limiting & Memory Management](#4-rate-limiting--memory-management)
5. [Error Handling Patterns](#5-error-handling-patterns)
6. [Database Schema for Job Tracking](#6-database-schema-for-job-tracking)
7. [Transaction Ordering (Critical)](#7-transaction-ordering-critical)
8. [Auto-Recovery Patterns](#8-auto-recovery-patterns)
9. [Statistics Synchronization](#9-statistics-synchronization)
10. [Best Practices Checklist](#10-best-practices-checklist)
11. [Common Pitfalls & Solutions](#11-common-pitfalls--solutions)
12. [Complete Code Examples](#12-complete-code-examples)

---

## 1. Initial Setup & Configuration

### 1.1 Dependencies

Add to `requirements.txt`:
```
apify-client>=1.4.0
fastapi>=0.100.0
sqlalchemy>=2.0.0
python-dotenv>=1.0.0
pydantic-settings>=2.0.0
```

### 1.2 Environment Configuration

Create `.env` file:
```env
# Apify Configuration
APIFY_API_KEY=your_api_key_here

# Database Configuration (example)
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=your_database
```

### 1.3 Settings Module

```python
# config/settings.py
"""Application configuration using environment variables."""

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Apify Configuration - REQUIRED
    apify_api_key: str = os.getenv("APIFY_API_KEY", "")

    # Database Configuration
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_user: str = os.getenv("DB_USER", "root")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_name: str = os.getenv("DB_NAME", "myapp")

    @property
    def database_url(self) -> str:
        return f"mysql+mysqlconnector://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"

settings = Settings()

def get_settings() -> Settings:
    return settings
```

### 1.4 Obtaining Apify API Key

1. Create account at https://apify.com
2. Go to Settings -> Integrations
3. Copy your API token
4. Store in `.env` file (NEVER commit to git)

---

## 2. Apify Client Implementation

### 2.1 Service Class

```python
# src/services/apify_client.py
"""
Apify API integration service using official apify-client library.

Key Features:
- Smart polling with exponential backoff (built into official client)
- Automatic retry with built-in backoff strategy
- Rate limiting handled by official client
- Simple one-line actor execution

IMPORTANT: The official apify-client is SYNCHRONOUS, so we wrap it
with asyncio.to_thread() for async compatibility.
"""

import asyncio
import logging
from typing import List
from apify_client import ApifyClient

logger = logging.getLogger(__name__)


class ApifyError(Exception):
    """Base exception for Apify API errors."""
    pass


class ApifyService:
    """
    Service for interacting with Apify API.

    The official client handles:
    - Smart polling with exponential backoff
    - Automatic retry on failures
    - Rate limiting (60 req/sec per resource)
    - Dataset retrieval
    """

    def __init__(
        self,
        api_key: str,
        actor_id: str = "scraper-mind~amazon-search-autocomplete-api"
    ):
        """
        Initialize Apify service.

        Args:
            api_key: Apify API token from Integrations page
            actor_id: Full actor ID (username~actor-name format)
                      NOTE: Use ~ (tilde), NOT / (slash)

        Raises:
            ValueError: If api_key is empty
        """
        if not api_key:
            raise ValueError("Apify API key is required")

        self.api_key = api_key
        self.actor_id = actor_id

        # Initialize official Apify client
        self.client = ApifyClient(token=api_key)

        logger.info(f"Initialized ApifyService with actor: {actor_id}")

    async def get_amazon_suggestions(
        self,
        query: str,
        use_prefix: bool = False,
        use_suffix: bool = False
    ) -> List[str]:
        """
        Get Amazon autocomplete suggestions for a search query.

        The official client's .call() method:
        1. Starts the actor run
        2. Waits for completion with smart polling (exponential backoff)
        3. Returns run metadata when complete

        Args:
            query: Search term (e.g., "whirlpool filter")
            use_prefix: Add alphabetic prefix to query
            use_suffix: Add alphabetic suffix to query

        Returns:
            List of unique suggestion strings

        Raises:
            ApifyError: If actor run fails
        """
        try:
            logger.info(f"[APIFY START] Query: '{query}'")

            # IMPORTANT: apify-client is synchronous
            # Wrap in asyncio.to_thread() for async compatibility
            run = await asyncio.to_thread(
                self.client.actor(self.actor_id).call,
                run_input={
                    'query': query,
                    'use_prefix': use_prefix,
                    'use_suffix': use_suffix
                }
            )

            run_id = run['id']
            dataset_id = run['defaultDatasetId']
            status = run['status']

            logger.info(f"[APIFY COMPLETE] Run {run_id} status: {status}")

            # CRITICAL: Check status before proceeding
            if status != 'SUCCEEDED':
                error_msg = f"Actor run failed with status: {status}"
                logger.error(f"[APIFY ERROR] {error_msg}")
                raise ApifyError(error_msg)

            # Retrieve results from dataset
            # Use iterate_items() for memory efficiency
            items = await asyncio.to_thread(
                lambda: list(self.client.dataset(dataset_id).iterate_items())
            )

            logger.info(f"[APIFY DEBUG] Retrieved {len(items)} items")

            # Extract suggestions from actor output
            # Format: [{"query": "X", "suggestion_01": "Y", ..., "suggestion_10": "Z"}]
            suggestions = []
            for item in items:
                for key, value in item.items():
                    if key.startswith('suggestion_') and value:
                        suggestions.append(value)

            # Deduplicate
            unique_suggestions = list(set(suggestions))

            logger.info(f"[APIFY RESULT] '{query}' -> {len(unique_suggestions)} suggestions")

            return unique_suggestions

        except Exception as e:
            logger.error(f"[APIFY ERROR] Failed for '{query}': {e}", exc_info=True)
            raise ApifyError(f"Failed to get suggestions: {e}") from e
```

### 2.2 Actor ID Format

**CRITICAL:** Use tilde (`~`) NOT slash (`/`) in actor IDs:
- Correct: `"scraper-mind~amazon-search-autocomplete-api"`
- Wrong: `"scraper-mind/amazon-search-autocomplete-api"`

### 2.3 Finding Actor IDs

1. Go to Apify Store: https://apify.com/store
2. Find your actor
3. Actor ID format: `{username}~{actor-name}`
4. Example: `apify~web-scraper`, `scraper-mind~amazon-search-autocomplete-api`

---

## 3. Background Worker Architecture

### 3.1 Thread-Based Worker (Recommended)

**Why NOT use APScheduler:**
- APScheduler fails silently with uvicorn --reload mode
- Creates master/worker process interference
- Scheduler may start in parent process that gets terminated

**Why Thread-Based Loop Works:**
- Simple threading.Thread with daemon=True
- Works with any uvicorn mode
- Reliable tick execution
- Immediate tick on startup

```python
# src/workers/scraper_worker.py
"""
Background worker for processing scraping jobs.

Architecture:
- Thread-based loop with 30-second interval
- Immediate tick on startup (fixes counter drift)
- Processes one job at a time to avoid API rate limits
"""

import logging
import asyncio
import threading
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Global worker thread and stop event
_worker_thread = None
_worker_stop = None


def scraper_worker_tick():
    """
    Worker tick function - called every 30 seconds.

    Wrapped in try/except to prevent worker thread from crashing.
    """
    try:
        logger.info(f"[WORKER TICK START] {datetime.utcnow()}")

        # Use shared database session
        from config.database import SessionLocal
        db = SessionLocal()

        try:
            # Expire stale state before querying
            db.expire_all()

            # Find all RUNNING jobs
            jobs = db.query(ScrapingJob).filter(
                ScrapingJob.status == JobStatus.RUNNING
            ).all()

            if not jobs:
                logger.debug("No RUNNING jobs found")
                return

            logger.info(f"[WORKER] Processing {len(jobs)} jobs")

            for job in jobs:
                try:
                    # Process job (run async code in sync context)
                    asyncio.run(process_scraping_job(db, job))
                except Exception as e:
                    logger.error(f"[JOB ERROR] Job #{job.id}: {e}", exc_info=True)
                    job.status = JobStatus.FAILED
                    job.error_message = str(e)
                    db.commit()

        finally:
            db.close()

    except Exception as e:
        logger.error(f"[WORKER TICK ERROR] {e}", exc_info=True)
        # Don't re-raise - let worker continue to next tick


def _worker_loop(stop_event: threading.Event, interval_seconds: int = 30):
    """
    Background worker loop.

    Args:
        stop_event: Threading event to signal shutdown
        interval_seconds: Seconds between ticks (default: 30)
    """
    logger.info(f"Worker thread started (interval: {interval_seconds}s)")

    # IMPORTANT: Run immediate tick on startup
    # This fixes any counter drift from previous crashes
    try:
        scraper_worker_tick()
    except Exception:
        logger.exception("[WORKER] immediate tick failed")

    # Then run every interval_seconds
    while not stop_event.wait(interval_seconds):
        try:
            scraper_worker_tick()
        except Exception:
            logger.exception("[WORKER] periodic tick failed")


def start_scraper_worker():
    """
    Start thread-based worker loop.

    Usage:
        @app.on_event("startup")
        async def startup_event():
            start_scraper_worker()
    """
    global _worker_thread, _worker_stop

    if _worker_thread and _worker_thread.is_alive():
        logger.warning("Worker already running")
        return

    _worker_stop = threading.Event()
    _worker_thread = threading.Thread(
        target=_worker_loop,
        args=(_worker_stop,),
        name="scraper-worker",
        daemon=True  # Allows clean exit
    )
    _worker_thread.start()
    logger.info("Worker started (thread-based, 30s interval)")


def stop_scraper_worker():
    """
    Stop the background worker.

    Usage:
        @app.on_event("shutdown")
        async def shutdown_event():
            stop_scraper_worker()
    """
    global _worker_thread, _worker_stop

    if not _worker_thread:
        return

    _worker_stop.set()
    _worker_thread.join(timeout=10)
    _worker_thread = None
    _worker_stop = None
    logger.info("Worker stopped")
```

### 3.2 Integration with FastAPI

```python
# main.py
from fastapi import FastAPI
from src.workers.scraper_worker import start_scraper_worker, stop_scraper_worker

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    start_scraper_worker()

@app.on_event("shutdown")
async def shutdown_event():
    stop_scraper_worker()
```

---

## 4. Rate Limiting & Memory Management

### 4.1 The Memory Limit Problem

**Problem Encountered:** 72% of rows completing with 0 keywords, all with 1-second durations.

**Root Cause:** Apify free tier has 8GB memory limit for ALL concurrent actor runs. Each actor run requests ~4GB memory. Without delay between requests, memory limit is exhausted.

**Error Message:**
```
"By launching this job you will exceed the memory limit of 8192MB
for all your Actor runs and builds (currently used: 8192MB, requested: 4096MB)."
```

### 4.2 Solution: Configurable Delay

Add delay between Apify API calls:

```python
# In your worker processing loop
async def process_row(db, row, job, apify_service):
    for variation in keyword_variations:
        try:
            suggestions = await apify_service.get_amazon_suggestions(variation)
            all_keywords.update(suggestions)

            # CRITICAL: Add delay between API calls
            if job.apify_delay_seconds > 0:
                logger.debug(f"Waiting {job.apify_delay_seconds}s...")
                await asyncio.sleep(job.apify_delay_seconds)

        except ApifyError as e:
            failed_variations += 1
            continue  # Continue with next variation
```

### 4.3 Database Schema for Delay

```sql
ALTER TABLE scraping_jobs
ADD COLUMN apify_delay_seconds INT DEFAULT 10
COMMENT 'Seconds to wait between Apify API calls';
```

### 4.4 User Control via UI

```python
# In your upload endpoint
@router.post("/upload")
async def upload_csv(
    file: UploadFile,
    job_name: str = Form(...),
    apify_delay_seconds: int = Form(10, description="Delay between API calls (0-60)"),
    db: Session = Depends(get_db)
):
    # Validate range
    apify_delay_seconds = max(0, min(60, apify_delay_seconds))

    job = ScrapingJob(
        job_name=job_name,
        apify_delay_seconds=apify_delay_seconds,
        # ...
    )
```

### 4.5 Recommended Delay Settings

| Environment | Delay | Notes |
|-------------|-------|-------|
| Development | 10-15s | Reasonable balance |
| Production (light) | 10s | Low concurrent jobs |
| Production (heavy) | 20-30s | Many concurrent jobs |
| Free tier | 30-60s | Conservative, safer |
| Paid tier | 5-10s | More memory available |

---

## 5. Error Handling Patterns

### 5.1 Per-Variation Failure Handling

Don't fail entire row if one variation fails:

```python
async def process_row(db, row, job, apify_service):
    all_keywords = set()
    successful_variations = 0
    failed_variations = 0
    last_error = None

    for variation in variations:
        try:
            suggestions = await apify_service.get_amazon_suggestions(variation)
            all_keywords.update(suggestions)
            successful_variations += 1

        except ApifyError as e:
            failed_variations += 1
            last_error = str(e)
            logger.error(f"Variation '{variation}' failed: {e}")
            continue  # Continue with next variation

    # Check if ALL variations failed
    if successful_variations == 0 and failed_variations > 0:
        row.status = RowStatus.FAILED
        row.error_message = last_error  # Store for user visibility
        job.failed_rows += 1
    else:
        # At least some succeeded
        row.status = RowStatus.COMPLETED
        row.keywords_found = len(all_keywords)
        job.completed_rows += 1
```

### 5.2 Error Message Storage

Always store error messages for debugging:

```python
# In your row model
class ScrapingRow(Base):
    __tablename__ = "scraping_rows"

    id = Column(BigInteger, primary_key=True)
    error_message = Column(Text, nullable=True)  # Store error details
    # ...
```

### 5.3 Row-Level Retry Endpoint

Allow users to retry individual rows:

```python
@router.post("/{job_id}/retry-row/{row_id}")
def retry_row(job_id: int, row_id: int, db: Session = Depends(get_db)):
    """Reset row to PENDING for reprocessing."""
    row = db.query(ScrapingRow).filter(
        ScrapingRow.id == row_id,
        ScrapingRow.job_id == job_id
    ).first()

    if not row:
        raise HTTPException(404, "Row not found")

    # Adjust job counters
    job = db.query(ScrapingJob).get(job_id)
    if row.status == RowStatus.COMPLETED:
        job.completed_rows = max(0, job.completed_rows - 1)
    elif row.status == RowStatus.FAILED:
        job.failed_rows = max(0, job.failed_rows - 1)

    # Reset row
    row.status = RowStatus.PENDING
    row.error_message = None
    row.keywords_found = 0
    row.started_at = None
    row.completed_at = None

    # Set job back to RUNNING if completed
    if job.status == JobStatus.COMPLETED:
        job.status = JobStatus.RUNNING
        job.completed_at = None

    db.commit()

    return {"message": f"Row #{row.row_number} reset to PENDING"}
```

---

## 6. Database Schema for Job Tracking

### 6.1 Scraping Jobs Table

```sql
CREATE TABLE scraping_jobs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    total_rows INT DEFAULT 0,
    completed_rows INT DEFAULT 0,
    failed_rows INT DEFAULT 0,

    -- Apify Configuration
    use_prefix BOOLEAN DEFAULT FALSE,
    use_suffix BOOLEAN DEFAULT FALSE,
    variation_level INT DEFAULT 1,
    apify_delay_seconds INT DEFAULT 10,

    -- Timestamps
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    archived_at TIMESTAMP NULL,

    -- Error Tracking
    error_message TEXT,

    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_archived_at (archived_at)
);
```

### 6.2 Scraping Rows Table

```sql
CREATE TABLE scraping_rows (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id BIGINT NOT NULL,
    row_number INT NOT NULL,
    part_number VARCHAR(50) NOT NULL,
    seed_keywords JSON NOT NULL,

    -- Status
    status VARCHAR(20) DEFAULT 'pending',
    keywords_found INT DEFAULT 0,

    -- Apify Tracking
    apify_run_id VARCHAR(50) NULL,  -- For stuck row detection

    -- Timestamps
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,

    -- Error Tracking
    error_message TEXT,

    FOREIGN KEY (job_id) REFERENCES scraping_jobs(id) ON DELETE CASCADE,
    INDEX idx_job_id (job_id),
    INDEX idx_status (status)
);
```

### 6.3 Status Enums

```python
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
```

---

## 7. Transaction Ordering (Critical)

### 7.1 The Problem

**Bug:** Pipeline showing "0 keywords" despite keywords existing in database.

**Root Cause:** Transaction ordering error - count committed BEFORE keywords:

```python
# WRONG - Transaction ordering bug
for kw in unique_keywords:
    db.add(Keyword(...))  # Keywords staged but NOT committed

subproject.keyword_count = len(unique_keywords)
db.commit()  # <- Count committed FIRST

# If worker crashes here, keywords are lost but count persists
```

### 7.2 The Solution

**ALWAYS commit data BEFORE metadata:**

```python
# CORRECT - Keywords committed first
for kw in unique_keywords:
    db.add(Keyword(...))

# Commit keywords FIRST
db.commit()

# THEN update count (can be recalculated if needed)
subproject.keyword_count = len(unique_keywords)
db.commit()
```

### 7.3 Principle

**"Save data first, metadata second"**

- If crash happens between commits, data persists
- Count can always be recalculated from actual keywords
- Better to have count=0 with keywords than count>0 without keywords

---

## 8. Auto-Recovery Patterns

### 8.1 Stuck Row Detection

**Problem:** Row status = RUNNING but apify_run_id = None, stuck for 1.5+ hours.

**Cause:** Worker crashed AFTER setting status to RUNNING but BEFORE calling Apify.

**Solution:** Auto-detect and recover stuck rows:

```python
def detect_and_recover_stuck_rows(db: Session, job: ScrapingJob):
    """
    Find and recover rows stuck in RUNNING state with no Apify run.

    Detection criteria:
    - Status = RUNNING
    - apify_run_id = None (no Apify run was started)
    - started_at > 10 minutes ago (been stuck long enough)
    """
    stuck_timeout = datetime.utcnow() - timedelta(minutes=10)

    stuck_rows = db.query(ScrapingRow).filter(
        ScrapingRow.job_id == job.id,
        ScrapingRow.status == RowStatus.RUNNING,
        ScrapingRow.apify_run_id == None,
        ScrapingRow.started_at < stuck_timeout
    ).all()

    for row in stuck_rows:
        logger.warning(f"[STUCK ROW] Row #{row.row_number} recovering")
        row.status = RowStatus.PENDING  # Reset to PENDING
        row.started_at = None
        row.error_message = "Auto-recovered from stuck state"

    if stuck_rows:
        db.commit()
```

### 8.2 Why 10-Minute Timeout?

- Normal Apify calls: 30-60 seconds
- Network delays: Can add 1-2 minutes
- 10 minutes: Generous buffer, prevents false positives

### 8.3 Why Reset to PENDING (not FAILED)?

- Gives row another chance
- Worker will retry on next tick
- User can manually fail if it keeps failing

---

## 9. Statistics Synchronization

### 9.1 The Counter Drift Problem

**Problem:** Job shows 53/200 completed, but database has 200/200 rows completed.

**Cause:** Worker increments counters in-memory, but crashes lose the counter update while row status persists.

### 9.2 Solution: Periodic Sync

```python
def sync_job_statistics(db: Session, job: ScrapingJob):
    """
    Synchronize job counters with actual database row counts.

    Call this at the start of each worker tick.
    """
    # Count actual row statuses from database (source of truth)
    completed_count = db.query(ScrapingRow).filter(
        ScrapingRow.job_id == job.id,
        ScrapingRow.status == RowStatus.COMPLETED
    ).count()

    failed_count = db.query(ScrapingRow).filter(
        ScrapingRow.job_id == job.id,
        ScrapingRow.status == RowStatus.FAILED
    ).count()

    # Check if out of sync
    if job.completed_rows != completed_count or job.failed_rows != failed_count:
        logger.warning(
            f"[STATS SYNC] Job #{job.id} - "
            f"Completed: {job.completed_rows} -> {completed_count}, "
            f"Failed: {job.failed_rows} -> {failed_count}"
        )

        job.completed_rows = completed_count
        job.failed_rows = failed_count

        # Auto-complete if all rows done
        if completed_count + failed_count >= job.total_rows:
            if job.status == JobStatus.RUNNING:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.utcnow()

        db.commit()
```

### 9.3 Integration

Call sync at the start of job processing:

```python
async def process_scraping_job(db: Session, job: ScrapingJob):
    # ALWAYS sync first
    sync_job_statistics(db, job)
    db.refresh(job)  # Reload with updated counters

    # Then process rows...
```

---

## 10. Best Practices Checklist

### Setup
- [ ] Add `apify-client>=1.4.0` to requirements.txt
- [ ] Store API key in `.env` (never commit)
- [ ] Use `~` (tilde) in actor IDs, not `/` (slash)
- [ ] Validate API key on service initialization

### Error Handling
- [ ] Catch ApifyError separately from general exceptions
- [ ] Store error messages in database for visibility
- [ ] Continue processing other variations on individual failures
- [ ] Provide row-level retry functionality

### Rate Limiting
- [ ] Add configurable delay between Apify calls
- [ ] Default to 10 seconds, allow 0-60 range
- [ ] Document memory limit considerations
- [ ] Use sequential processing, not parallel

### Database
- [ ] Track apify_run_id for stuck row detection
- [ ] Store error_message for debugging
- [ ] Use CASCADE delete for related records
- [ ] Add indexes on status and timestamp columns

### Worker
- [ ] Use thread-based loop, NOT APScheduler
- [ ] Run immediate tick on startup
- [ ] Sync statistics every tick
- [ ] Detect and recover stuck rows

### Transactions
- [ ] Commit data BEFORE metadata
- [ ] Refresh objects after commit
- [ ] Use db.expire_all() to clear stale state

### Logging
- [ ] Use prefixed log messages: [APIFY START], [APIFY ERROR], etc.
- [ ] Log query, results count, and duration
- [ ] Log sync corrections
- [ ] Log stuck row recovery

---

## 11. Common Pitfalls & Solutions

### Pitfall 1: Silent APScheduler Failure
**Problem:** Scheduler starts but never fires ticks with uvicorn --reload
**Solution:** Use thread-based worker loop instead

### Pitfall 2: Memory Limit Exhaustion
**Problem:** 72% of rows complete with 0 keywords
**Solution:** Add 10-30 second delay between Apify calls

### Pitfall 3: Stuck RUNNING Rows
**Problem:** Rows stuck in RUNNING forever
**Solution:** Auto-detect rows with no apify_run_id after 10 minutes

### Pitfall 4: Counter Drift
**Problem:** Job shows wrong completion count
**Solution:** Sync counters with database on every tick

### Pitfall 5: Lost Keywords
**Problem:** Count > 0 but no keywords in database
**Solution:** Commit keywords BEFORE updating count

### Pitfall 6: Synchronous Client in Async Code
**Problem:** Blocking the event loop
**Solution:** Wrap client calls with `asyncio.to_thread()`

### Pitfall 7: Wrong Actor ID Format
**Problem:** "Actor not found" error
**Solution:** Use `username~actor-name` NOT `username/actor-name`

### Pitfall 8: Detached SQLAlchemy Objects
**Problem:** "Instance is not bound to a Session"
**Solution:** Call `db.refresh(object)` after commit

### Pitfall 9: No Error Visibility
**Problem:** Users don't know why rows failed
**Solution:** Store and display error_message

### Pitfall 10: No Retry Capability
**Problem:** Users must recreate entire job for one failed row
**Solution:** Implement per-row retry endpoint

---

## 12. Complete Code Examples

### 12.1 Full Job Processing Flow

```python
# src/workers/scraper_worker.py - Complete processing example

async def process_scraping_job(db: Session, job: ScrapingJob):
    """
    Complete job processing with all safety patterns.
    """
    job_start_time = datetime.utcnow()
    logger.info(f"[JOB START] Job #{job.id}: {job.job_name}")

    # 1. ALWAYS sync statistics first
    sync_job_statistics(db, job)
    db.refresh(job)

    # 2. Initialize Apify service
    settings = get_settings()
    apify_service = ApifyService(api_key=settings.apify_api_key)

    # 3. Get pending rows (use PENDING filter, not RUNNING)
    rows = db.query(ScrapingRow).filter(
        ScrapingRow.job_id == job.id,
        ScrapingRow.status == RowStatus.PENDING
    ).order_by(ScrapingRow.row_number).all()

    logger.info(f"[JOB] {len(rows)} pending rows to process")

    # 4. Process each row
    for row in rows:
        # Check if job was paused/cancelled
        db.refresh(job)
        if job.status in [JobStatus.PAUSED, JobStatus.CANCELLED]:
            logger.info(f"[JOB] Job #{job.id} {job.status}, stopping")
            break

        # Atomic claim: Set to RUNNING
        db.refresh(row)
        if row.status != RowStatus.PENDING:
            continue  # Already claimed by another process

        row.status = RowStatus.RUNNING
        row.started_at = datetime.utcnow()
        db.commit()

        # CRITICAL: Refresh after commit
        db.refresh(row)
        db.refresh(job)

        # Process with timeout (10 minutes max)
        try:
            await asyncio.wait_for(
                process_scraping_row(db, row, job, apify_service),
                timeout=600
            )
        except asyncio.TimeoutError:
            logger.error(f"[TIMEOUT] Row #{row.row_number}")
            row.status = RowStatus.FAILED
            row.error_message = "Timed out after 10 minutes"
            row.completed_at = datetime.utcnow()
            job.failed_rows += 1
            db.commit()

    # 5. Update job final status
    db.refresh(job)
    if job.status == JobStatus.CANCELLED:
        pass  # Don't overwrite
    elif job.failed_rows == job.total_rows:
        job.status = JobStatus.FAILED
        job.error_message = "All rows failed"
        job.completed_at = datetime.utcnow()
    elif job.completed_rows + job.failed_rows >= job.total_rows:
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()

    db.commit()

    duration = (datetime.utcnow() - job_start_time).total_seconds()
    logger.info(
        f"[JOB COMPLETE] Job #{job.id}: "
        f"{job.completed_rows} completed, {job.failed_rows} failed | "
        f"Duration: {duration:.2f}s"
    )
```

### 12.2 Complete Row Processing with Keyword Variations

```python
def generate_keyword_variations(
    base_keyword: str,
    use_prefix: bool = False,
    use_suffix: bool = False,
    variation_level: int = 1
) -> List[str]:
    """
    Generate keyword variations for expanded search coverage.

    Args:
        base_keyword: Original keyword (e.g., "whirlpool filter")
        use_prefix: Add prefix variations (e.g., "a whirlpool filter")
        use_suffix: Add suffix variations (e.g., "whirlpool filter a")
        variation_level: Depth of variations
            - 1: a-z (26 variations)
            - 2: aa-zz (676 variations)
            - 3: aaa-zzz (17,576 variations) - USE WITH CAUTION

    Returns:
        List of keyword variations (always includes base keyword)
    """
    import itertools
    import string

    variations = [base_keyword]  # Always include original

    if not use_prefix and not use_suffix:
        return variations

    # Generate variation strings based on level
    if variation_level == 1:
        var_strings = list(string.ascii_lowercase)  # a-z
    elif variation_level == 2:
        var_strings = [
            ''.join(combo)
            for combo in itertools.product(string.ascii_lowercase, repeat=2)
        ]  # aa-zz
    elif variation_level == 3:
        var_strings = [
            ''.join(combo)
            for combo in itertools.product(string.ascii_lowercase, repeat=3)
        ]  # aaa-zzz - WARNING: 17,576 variations!
    else:
        var_strings = list(string.ascii_lowercase)

    if use_prefix:
        for var in var_strings:
            variations.append(f"{var} {base_keyword}")

    if use_suffix:
        for var in var_strings:
            variations.append(f"{base_keyword} {var}")

    logger.debug(f"Generated {len(variations)} variations for '{base_keyword}'")
    return variations


async def process_scraping_row(
    db: Session,
    row: ScrapingRow,
    job: ScrapingJob,
    apify_service: ApifyService
) -> None:
    """
    Process a single scraping row with full error handling.
    """
    try:
        start_time = datetime.utcnow()
        logger.info(
            f"[ROW START] Row #{row.row_number}: "
            f"{row.part_number} with {len(row.seed_keywords)} seeds"
        )

        all_keywords: Set[str] = set()
        successful_variations = 0
        failed_variations = 0
        last_error = None

        # Process each seed keyword
        for seed_keyword in row.seed_keywords:
            variations = generate_keyword_variations(
                base_keyword=seed_keyword,
                use_prefix=job.use_prefix,
                use_suffix=job.use_suffix,
                variation_level=job.variation_level
            )

            # Call Apify for each variation
            for variation in variations:
                try:
                    suggestions = await apify_service.get_amazon_suggestions(
                        query=variation,
                        use_prefix=False,  # Already handled
                        use_suffix=False
                    )

                    all_keywords.update(suggestions)
                    successful_variations += 1

                    # CRITICAL: Delay between API calls
                    if job.apify_delay_seconds > 0:
                        await asyncio.sleep(job.apify_delay_seconds)

                except ApifyError as e:
                    failed_variations += 1
                    last_error = str(e)
                    logger.error(f"Variation '{variation}' failed: {e}")
                    continue  # Continue with next variation

        scraped_keywords = sorted(list(all_keywords))
        logger.info(
            f"Row #{row.row_number}: {len(scraped_keywords)} keywords | "
            f"Success: {successful_variations}, Failed: {failed_variations}"
        )

        # Determine row status
        if successful_variations == 0 and failed_variations > 0:
            # ALL variations failed
            row.status = RowStatus.FAILED
            row.completed_at = datetime.utcnow()
            row.error_message = last_error
            row.keywords_found = 0
            job.failed_rows += 1
            logger.error(f"[ROW FAILED] Row #{row.row_number}: All failed")
        else:
            # At least some succeeded - store keywords
            for keyword_text in scraped_keywords:
                existing = db.query(Keyword).filter(
                    Keyword.subproject_id == row.subproject_id,
                    Keyword.keyword == keyword_text
                ).first()

                if not existing:
                    keyword = Keyword(
                        subproject_id=row.subproject_id,
                        keyword=keyword_text,
                        source=KeywordSource.SCRAPED,
                        status=KeywordStatus.INCLUDED
                    )
                    db.add(keyword)

            row.keywords_found = len(scraped_keywords)
            row.status = RowStatus.COMPLETED
            row.completed_at = datetime.utcnow()
            row.error_message = None
            job.completed_rows += 1

        # CRITICAL: Commit keywords FIRST
        db.commit()

        # THEN update count (can be recalculated if needed)
        SubprojectService.update_keyword_count(db, row.subproject_id)

        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"[ROW COMPLETE] Row #{row.row_number}: {duration:.2f}s")

    except Exception as e:
        logger.error(f"[ROW ERROR] Row #{row.row_number}: {e}", exc_info=True)
        row.status = RowStatus.FAILED
        row.completed_at = datetime.utcnow()
        row.error_message = str(e)
        job.failed_rows += 1
        db.commit()
```

### 12.3 Complete FastAPI Upload Endpoint

```python
# src/api/scraper.py

@router.post("/upload", response_model=JobResponse, status_code=201)
async def upload_csv(
    file: UploadFile = File(..., description="CSV file"),
    job_name: str = Form(..., description="Human-readable job name"),
    skip_header: bool = Form(False, description="Skip first row"),
    use_prefix: bool = Form(False, description="Enable prefix variations"),
    use_suffix: bool = Form(False, description="Enable suffix variations"),
    variation_level: int = Form(1, description="Variation depth (1-3)"),
    apify_delay_seconds: int = Form(10, description="Delay between calls (0-60)"),
    db: Session = Depends(get_db)
):
    """
    Upload CSV file and create scraping job.

    CSV Format:
        Part Number, Keyword1, Keyword2, Keyword3
        WF-UKF8001, whirlpool filter, refrigerator filter
        WF-4396508, edr5rxd1, replacement filter
    """
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(400, "Only CSV files accepted")

        # Validate and clamp delay
        apify_delay_seconds = max(0, min(60, apify_delay_seconds))

        # Parse CSV
        content = await file.read()
        csv_data = parse_csv(content.decode('utf-8'), skip_header)

        # Create job
        job = ScrapingJob(
            job_name=job_name,
            status=JobStatus.PENDING,
            total_rows=len(csv_data),
            use_prefix=use_prefix,
            use_suffix=use_suffix,
            variation_level=variation_level,
            apify_delay_seconds=apify_delay_seconds
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Create rows
        for i, row_data in enumerate(csv_data, 1):
            part_number = row_data[0]
            seed_keywords = [kw.strip() for kw in row_data[1:] if kw.strip()]

            # Create or find subproject
            subproject = find_or_create_subproject(db, part_number, seed_keywords[0])

            row = ScrapingRow(
                job_id=job.id,
                subproject_id=subproject.id,
                row_number=i,
                part_number=part_number,
                seed_keywords=seed_keywords,
                status=RowStatus.PENDING
            )
            db.add(row)

        db.commit()

        return JobResponse(
            job_id=job.id,
            job_name=job.job_name,
            status=job.status.value,
            total_rows=job.total_rows,
            completed_rows=0,
            failed_rows=0,
            percentage=0.0
        )

    except CSVParseError as e:
        raise HTTPException(400, str(e))
```

### 12.4 SQLAlchemy Models

```python
# src/models/scraping_jobs.py

from enum import Enum
from sqlalchemy import Column, BigInteger, String, Integer, Boolean, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from config.database import Base

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ScrapingJob(Base):
    __tablename__ = "scraping_jobs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_name = Column(String(255), nullable=False)
    status = Column(String(20), default="pending")

    # Progress tracking
    total_rows = Column(Integer, default=0)
    completed_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)

    # Apify configuration
    use_prefix = Column(Boolean, default=False)
    use_suffix = Column(Boolean, default=False)
    variation_level = Column(Integer, default=1)
    apify_delay_seconds = Column(Integer, default=10)

    # Timestamps
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")
    updated_at = Column(TIMESTAMP, onupdate="CURRENT_TIMESTAMP")
    archived_at = Column(TIMESTAMP, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Relationships
    rows = relationship("ScrapingRow", back_populates="job", cascade="all, delete-orphan")


# src/models/scraping_rows.py

class RowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ScrapingRow(Base):
    __tablename__ = "scraping_rows"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(BigInteger, ForeignKey("scraping_jobs.id", ondelete="CASCADE"))
    subproject_id = Column(BigInteger, ForeignKey("subprojects.id", ondelete="CASCADE"))
    row_number = Column(Integer, nullable=False)
    part_number = Column(String(50), nullable=False)
    seed_keywords = Column(JSON, nullable=False)  # List of keywords

    # Status
    status = Column(String(20), default="pending")
    keywords_found = Column(Integer, default=0)

    # For stuck row detection
    apify_run_id = Column(String(50), nullable=True)

    # Timestamps
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Relationships
    job = relationship("ScrapingJob", back_populates="rows")
```

### 12.5 main.py Integration

```python
# main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.workers.scraper_worker import start_scraper_worker, stop_scraper_worker
from src.api import scraper, projects, keywords

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    start_scraper_worker()
    yield
    # Shutdown
    stop_scraper_worker()

app = FastAPI(
    title="Listings Workflow",
    description="Enterprise listings management with Apify integration",
    lifespan=lifespan
)

# Register routers
app.include_router(scraper.router)
app.include_router(projects.router)
app.include_router(keywords.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=True  # Works with thread-based worker!
    )
```

---

## Summary

This documentation captures lessons learned from production use of Apify with FastAPI. The key patterns are:

1. **Thread-based worker** over APScheduler for reliability
2. **Configurable delay** between API calls for memory management
3. **Per-variation error handling** for resilience
4. **Statistics synchronization** for accuracy
5. **Stuck row detection** for recovery
6. **Transaction ordering** for data integrity

Following these patterns will help avoid the issues discovered during development and create a robust Apify integration.
