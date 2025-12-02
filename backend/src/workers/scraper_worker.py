# =============================================================================
# Workers Domain - Scraper Background Worker
# =============================================================================
# Purpose: Process scrape jobs in background using thread-based worker
# Public API: start_worker, stop_worker
# Dependencies: threading, sqlalchemy, apify.client, jobs.service
# =============================================================================

import asyncio
import logging
import threading
from datetime import datetime
from typing import Optional

from ..config import settings
from ..database import SessionLocal
from ..jobs.models import ScrapeJob, JobAsin
from ..jobs.service import JobService
from ..reviews.service import ReviewService
from ..apify.client import get_apify_service
from ..apify.exceptions import ApifyError


logger = logging.getLogger(__name__)


# ===== Worker State =====
_worker_thread: Optional[threading.Thread] = None
_stop_event: Optional[threading.Event] = None


# ===== Worker Control =====

def start_worker() -> None:
    """
    Start the background worker thread.

    Worker processes one job at a time, checking every WORKER_INTERVAL_SECONDS.
    Uses threading.Event for graceful shutdown (not APScheduler).
    """
    global _worker_thread, _stop_event

    if _worker_thread and _worker_thread.is_alive():
        logger.warning("Worker already running")
        return

    _stop_event = threading.Event()
    _worker_thread = threading.Thread(
        target=_worker_loop,
        args=(_stop_event, settings.worker_interval_seconds),
        daemon=True,
        name="scraper-worker",
    )
    _worker_thread.start()
    logger.info("Scraper worker started")


def stop_worker() -> None:
    """Stop the background worker gracefully."""
    global _worker_thread, _stop_event

    if _stop_event:
        _stop_event.set()

    if _worker_thread:
        _worker_thread.join(timeout=5.0)
        logger.info("Scraper worker stopped")


# ===== Worker Loop =====

def _worker_loop(stop_event: threading.Event, interval_seconds: int) -> None:
    """
    Main worker loop.

    Runs immediately on start, then every interval_seconds.
    """
    logger.info(f"Worker loop starting with {interval_seconds}s interval")

    # Immediate tick on startup
    _worker_tick()

    # Then every interval_seconds
    while not stop_event.wait(interval_seconds):
        _worker_tick()


def _worker_tick() -> None:
    """
    Single worker tick - process one job or sync stats.

    This is the main work function called each interval.
    """
    db = SessionLocal()
    try:
        job_service = JobService(db)

        # Sync stats for running jobs
        _sync_running_jobs(db, job_service)

        # Check for stuck jobs (running for > 30 minutes)
        _recover_stuck_jobs(db)

        # Get next queued job
        job = job_service.get_queued_job()
        if not job:
            return

        logger.info(f"Processing job {job.id}: {job.job_name}")

        # Process job
        _process_job(db, job)

    except Exception as e:
        logger.error(f"Worker tick error: {e}", exc_info=True)
    finally:
        db.close()


# ===== Job Processing =====

def _process_job(db, job: ScrapeJob) -> None:
    """
    Process a single scrape job.

    Iterates through ASINs, calls Apify, saves reviews.
    """
    job_service = JobService(db)
    review_service = ReviewService(db)
    apify_service = get_apify_service()

    # Mark job as running
    job_service.start_job(job)

    try:
        # Process each pending ASIN
        while True:
            asin_record = job_service.get_pending_asin(job.id)
            if not asin_record:
                break

            _process_asin(
                db=db,
                job=job,
                asin_record=asin_record,
                apify_service=apify_service,
                review_service=review_service,
                job_service=job_service,
            )

            # Sync stats after each ASIN
            job_service.sync_job_stats(job)

        # Determine final status
        db.refresh(job)
        if job.failed_asins > 0 and job.completed_asins > 0:
            job_service.complete_job(job, partial=True)
        elif job.failed_asins > 0:
            job_service.fail_job(job, "All ASINs failed to process")
        else:
            job_service.complete_job(job)

        logger.info(
            f"Job {job.id} completed: "
            f"{job.completed_asins} succeeded, {job.failed_asins} failed, "
            f"{job.total_reviews} reviews"
        )

    except Exception as e:
        logger.error(f"Job {job.id} failed: {e}", exc_info=True)
        job_service.fail_job(job, str(e))


def _process_asin(
    db,
    job: ScrapeJob,
    asin_record: JobAsin,
    apify_service,
    review_service: ReviewService,
    job_service: JobService,
) -> None:
    """
    Process a single ASIN within a job.

    Handles multiple star filters with deduplication.
    """
    asin = asin_record.asin
    logger.info(f"Processing ASIN {asin} for job {job.id}")

    # Mark ASIN as running
    asin_record.status = "running"
    asin_record.started_at = datetime.utcnow()
    db.commit()

    try:
        all_reviews = []
        seen_review_ids = set()

        # Get star filters
        star_filters = job.star_filters or ["all_stars"]

        # Run Apify for each star filter
        for star_filter in star_filters:
            try:
                # Call Apify synchronously (it handles async internally)
                reviews = asyncio.run(
                    apify_service.scrape_reviews(
                        asin=asin,
                        domain_code=job.marketplace,
                        sort_by=job.sort_by,
                        max_pages=job.max_pages,
                        filter_by_star=star_filter,
                        keyword_filter=job.keyword_filter,
                        reviewer_type=job.reviewer_type,
                    )
                )

                # Deduplicate by review ID
                for review in reviews:
                    review_id = review.get("reviewId")
                    if review_id and review_id in seen_review_ids:
                        continue
                    if review_id:
                        seen_review_ids.add(review_id)
                    all_reviews.append(review)

                    # Get product title from first review
                    if not asin_record.product_title and review.get("productTitle"):
                        asin_record.product_title = review["productTitle"]

                logger.info(f"Star filter '{star_filter}': {len(reviews)} reviews")

                # Delay between API calls
                if job.apify_delay_seconds > 0 and len(star_filters) > 1:
                    import time
                    time.sleep(job.apify_delay_seconds)

            except ApifyError as e:
                logger.warning(f"Star filter '{star_filter}' failed for {asin}: {e}")
                continue

        # Save reviews
        saved_count = review_service.save_reviews(asin_record, all_reviews)

        # Update ASIN record
        asin_record.status = "completed"
        asin_record.reviews_found = saved_count
        asin_record.completed_at = datetime.utcnow()
        db.commit()

        # Update ASIN history
        job_service.update_asin_history(asin, job.marketplace, job.id)

        logger.info(f"ASIN {asin} completed: {saved_count} reviews saved")

    except Exception as e:
        logger.error(f"ASIN {asin} failed: {e}", exc_info=True)
        asin_record.status = "failed"
        asin_record.error_message = str(e)
        asin_record.completed_at = datetime.utcnow()
        db.commit()


# ===== Helper Functions =====

def _sync_running_jobs(db, job_service: JobService) -> None:
    """Sync statistics for all running jobs."""
    running_jobs = (
        db.query(ScrapeJob)
        .filter(ScrapeJob.status == "running")
        .all()
    )

    for job in running_jobs:
        job_service.sync_job_stats(job)


def _recover_stuck_jobs(db) -> None:
    """
    Recover jobs stuck in running state.

    Marks jobs running for > 30 minutes as failed.
    """
    from datetime import timedelta

    threshold = datetime.utcnow() - timedelta(minutes=30)

    stuck_jobs = (
        db.query(ScrapeJob)
        .filter(
            ScrapeJob.status == "running",
            ScrapeJob.started_at < threshold,
        )
        .all()
    )

    for job in stuck_jobs:
        logger.warning(f"Recovering stuck job {job.id}")
        job.status = "failed"
        job.error_message = "Job timed out (stuck for > 30 minutes)"
        job.completed_at = datetime.utcnow()

    if stuck_jobs:
        db.commit()
