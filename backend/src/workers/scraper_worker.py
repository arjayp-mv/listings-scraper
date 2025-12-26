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
from ..product_scans.models import ProductScanJob, ProductScanItem, JobStatus, ItemStatus
from ..product_scans.service import ProductScanService
from ..channel_skus.service import ChannelSkuService
from ..competitors.models import CompetitorScrapeJob, CompetitorScrapeItem
from ..competitors.service import CompetitorService
from ..apify.client import get_apify_service, ApifyService
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
    Processes both review scrape jobs and product scan jobs.
    """
    db = SessionLocal()
    try:
        job_service = JobService(db)

        # Sync stats for running jobs
        _sync_running_jobs(db, job_service)

        # Check for stuck jobs (running for > 30 minutes)
        _recover_stuck_jobs(db)

        # Process review scrape jobs (existing functionality)
        review_job = job_service.get_queued_job()
        if review_job:
            logger.info(f"Processing review job {review_job.id}: {review_job.job_name}")
            _process_job(db, review_job)
            return

        # Process product scan jobs
        scan_service = ProductScanService(db)
        product_job = scan_service.get_next_queued_job()
        if product_job:
            logger.info(f"Processing product scan job {product_job.id}: {product_job.job_name}")
            _process_product_scan_job(db, product_job)
            return

        # Process competitor scrape jobs
        competitor_job = CompetitorService.get_next_queued_job(db)
        if competitor_job:
            logger.info(f"Processing competitor job {competitor_job.id}: {competitor_job.job_name}")
            _process_competitor_scrape_job(db, competitor_job)
            return

        # Check for scheduled competitor scrapes
        _check_scheduled_competitor_scrapes(db)

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

    # Recover stuck review scrape jobs
    stuck_jobs = (
        db.query(ScrapeJob)
        .filter(
            ScrapeJob.status == "running",
            ScrapeJob.started_at < threshold,
        )
        .all()
    )

    for job in stuck_jobs:
        logger.warning(f"Recovering stuck review job {job.id}")
        job.status = "failed"
        job.error_message = "Job timed out (stuck for > 30 minutes)"
        job.completed_at = datetime.utcnow()

    # Recover stuck product scan jobs
    stuck_scan_jobs = (
        db.query(ProductScanJob)
        .filter(
            ProductScanJob.status == JobStatus.RUNNING,
            ProductScanJob.started_at < threshold,
        )
        .all()
    )

    for job in stuck_scan_jobs:
        logger.warning(f"Recovering stuck product scan job {job.id}")
        job.status = JobStatus.FAILED
        job.error_message = "Job timed out (stuck for > 30 minutes)"
        job.completed_at = datetime.utcnow()

    # Recover stuck competitor scrape jobs
    stuck_competitor_jobs = (
        db.query(CompetitorScrapeJob)
        .filter(
            CompetitorScrapeJob.status == "running",
            CompetitorScrapeJob.started_at < threshold,
        )
        .all()
    )

    for job in stuck_competitor_jobs:
        logger.warning(f"Recovering stuck competitor job {job.id}")
        job.status = "failed"
        job.error_message = "Job timed out (stuck for > 30 minutes)"
        job.completed_at = datetime.utcnow()

    if stuck_jobs or stuck_scan_jobs or stuck_competitor_jobs:
        db.commit()


# ===== Product Scan Job Processing =====

PRODUCT_SCAN_BATCH_SIZE = 50  # URLs per Apify call


def _process_product_scan_job(db, job: ProductScanJob) -> None:
    """
    Process a product scan job.

    Batches ASINs together for efficient Apify calls.
    """
    scan_service = ProductScanService(db)
    channel_sku_service = ChannelSkuService(db)
    apify_service = get_apify_service()

    # Mark job as running
    scan_service.start_job(job)

    try:
        # Process pending items in batches
        while True:
            pending_items = scan_service.get_pending_items(
                job.id, limit=PRODUCT_SCAN_BATCH_SIZE
            )
            if not pending_items:
                break

            _process_product_scan_batch(
                db=db,
                job=job,
                items=pending_items,
                apify_service=apify_service,
                scan_service=scan_service,
                channel_sku_service=channel_sku_service,
            )

            # Delay between batches
            if settings.apify_delay_seconds > 0:
                import time
                time.sleep(settings.apify_delay_seconds)

        # Finalize job
        scan_service.complete_job(job)

        logger.info(
            f"Product scan job {job.id} completed: "
            f"{job.completed_listings} succeeded, {job.failed_listings} failed"
        )

    except Exception as e:
        logger.error(f"Product scan job {job.id} failed: {e}", exc_info=True)
        scan_service.fail_job(job, str(e))


def _process_product_scan_batch(
    db,
    job: ProductScanJob,
    items: list,
    apify_service: ApifyService,
    scan_service: ProductScanService,
    channel_sku_service: ChannelSkuService,
) -> None:
    """
    Process a batch of product scan items.

    Calls Apify once for all ASINs in the batch for efficiency.
    """
    # Build ASIN list and item map
    asins = [item.input_asin for item in items]
    item_map = {item.input_asin: item for item in items}

    # Mark all items as running
    for item in items:
        scan_service.mark_item_running(item)

    logger.info(f"Processing batch of {len(asins)} ASINs for job {job.id}")

    try:
        # Call Apify (synchronous version for worker thread)
        results = apify_service.scrape_product_details_sync(
            asins=asins,
            marketplace=job.marketplace,
        )

        # Process results
        results_map = {}
        for result in results:
            # Map result to ASIN
            result_asin = result.get("asin")
            result_url = result.get("url", "")

            # Try to extract ASIN from URL if not in result
            if not result_asin and result_url:
                import re
                match = re.search(r"/dp/([A-Z0-9]{10})", result_url)
                if match:
                    result_asin = match.group(1)

            if result_asin:
                results_map[result_asin] = result

        # Update each item
        for asin, item in item_map.items():
            result = results_map.get(asin)

            if result:
                status_code = result.get("statusCode", 0)

                if status_code == 200:
                    # Parse rating
                    rating = ApifyService.parse_rating(result.get("productRating"))

                    # Update item
                    scan_service.complete_item(
                        item=item,
                        rating=rating,
                        review_count=result.get("countReview"),
                        title=result.get("title"),
                        scraped_asin=result.get("asin"),
                        raw_data=result,
                    )

                    # Update Channel SKU metrics
                    channel_sku = item.channel_sku
                    if channel_sku:
                        channel_sku_service.update_metrics(
                            channel_sku=channel_sku,
                            rating=rating,
                            review_count=result.get("countReview"),
                            title=result.get("title"),
                            scraped_asin=result.get("asin"),
                            job_id=job.id,
                        )

                    logger.debug(f"ASIN {asin}: rating={rating}, reviews={result.get('countReview')}")

                else:
                    # Non-200 status
                    error_msg = result.get("statusMessage", f"Status code: {status_code}")
                    scan_service.fail_item(item, error_msg)
                    logger.warning(f"ASIN {asin} failed: {error_msg}")

            else:
                # No result found for this ASIN
                scan_service.fail_item(item, "No result returned from Apify")
                logger.warning(f"ASIN {asin}: No result in Apify response")

    except ApifyError as e:
        # Apify call failed - mark all items as failed
        logger.error(f"Apify batch call failed: {e}")
        for item in items:
            if item.status == ItemStatus.RUNNING:
                scan_service.fail_item(item, str(e))

    except Exception as e:
        logger.error(f"Batch processing error: {e}", exc_info=True)
        for item in items:
            if item.status == ItemStatus.RUNNING:
                scan_service.fail_item(item, str(e))


# ===== Competitor Scrape Job Processing =====

COMPETITOR_BATCH_SIZE = 50  # ASINs per Apify call


def _process_competitor_scrape_job(db, job: CompetitorScrapeJob) -> None:
    """
    Process a competitor scrape job.

    Batches competitor ASINs together for efficient Apify calls.
    """
    apify_service = get_apify_service()

    # Mark job as running
    job.status = "running"
    job.started_at = datetime.utcnow()
    db.commit()

    try:
        # Process pending items in batches
        while True:
            pending_items = CompetitorService.get_pending_items_for_job(db, job.id)
            if not pending_items:
                break

            # Take only batch size
            batch = pending_items[:COMPETITOR_BATCH_SIZE]

            _process_competitor_batch(
                db=db,
                job=job,
                items=batch,
                apify_service=apify_service,
            )

            # Delay between batches
            if settings.apify_delay_seconds > 0:
                import time
                time.sleep(settings.apify_delay_seconds)

        # Finalize job
        db.refresh(job)
        if job.failed_competitors > 0 and job.completed_competitors > 0:
            job.status = "partial"
        elif job.failed_competitors > 0 and job.completed_competitors == 0:
            job.status = "failed"
        else:
            job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

        logger.info(
            f"Competitor scrape job {job.id} completed: "
            f"{job.completed_competitors} succeeded, {job.failed_competitors} failed"
        )

    except Exception as e:
        logger.error(f"Competitor scrape job {job.id} failed: {e}", exc_info=True)
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()


def _process_competitor_batch(
    db,
    job: CompetitorScrapeJob,
    items: list,
    apify_service: ApifyService,
) -> None:
    """
    Process a batch of competitor scrape items.

    Calls Apify once for all ASINs in the batch for efficiency.
    """
    # Build ASIN list and item map
    asins = [item.input_asin for item in items]
    item_map = {item.input_asin: item for item in items}

    # Mark all items as running
    for item in items:
        item.status = "running"
        item.started_at = datetime.utcnow()
    db.commit()

    logger.info(f"Processing competitor batch of {len(asins)} ASINs for job {job.id}")

    try:
        # Call Apify (synchronous version for worker thread)
        results = apify_service.scrape_product_details_sync(
            asins=asins,
            marketplace=job.marketplace,
        )

        # Process results
        results_map = {}
        for result in results:
            # Map result to ASIN
            result_asin = result.get("asin")
            result_url = result.get("url", "")

            # Try to extract ASIN from URL if not in result
            if not result_asin and result_url:
                import re
                match = re.search(r"/dp/([A-Z0-9]{10})", result_url)
                if match:
                    result_asin = match.group(1)

            if result_asin:
                results_map[result_asin] = result

        # Update each item and save competitor data
        for asin, item in item_map.items():
            result = results_map.get(asin)
            competitor = item.competitor

            if result:
                status_code = result.get("statusCode", 0)

                if status_code == 200 or result.get("title"):
                    # Parse and save competitor data
                    pack_size = competitor.pack_size or 1 if competitor else 1
                    parsed_data = ApifyService.parse_competitor_data(result, pack_size)

                    # Save scraped data
                    CompetitorService.save_scraped_data(db, item.competitor_id, parsed_data)

                    # Record price history
                    CompetitorService.record_price_history(db, item.competitor_id)

                    # Update next scrape time if scheduled
                    if competitor and competitor.schedule != "none":
                        CompetitorService.update_next_scrape(db, competitor)

                    # Mark item as completed
                    item.status = "completed"
                    item.completed_at = datetime.utcnow()
                    job.completed_competitors += 1

                    logger.debug(
                        f"Competitor {asin}: price={parsed_data.get('price')}, "
                        f"rating={parsed_data.get('rating')}"
                    )

                else:
                    # Non-200 status
                    error_msg = result.get("statusMessage", f"Status code: {status_code}")
                    item.status = "failed"
                    item.error_message = error_msg
                    item.completed_at = datetime.utcnow()
                    job.failed_competitors += 1
                    logger.warning(f"Competitor {asin} failed: {error_msg}")

            else:
                # No result found for this ASIN
                item.status = "failed"
                item.error_message = "No result returned from Apify"
                item.completed_at = datetime.utcnow()
                job.failed_competitors += 1
                logger.warning(f"Competitor {asin}: No result in Apify response")

        db.commit()

    except ApifyError as e:
        # Apify call failed - mark all items as failed
        logger.error(f"Apify competitor batch call failed: {e}")
        for item in items:
            if item.status == "running":
                item.status = "failed"
                item.error_message = str(e)
                item.completed_at = datetime.utcnow()
                job.failed_competitors += 1
        db.commit()

    except Exception as e:
        logger.error(f"Competitor batch processing error: {e}", exc_info=True)
        for item in items:
            if item.status == "running":
                item.status = "failed"
                item.error_message = str(e)
                item.completed_at = datetime.utcnow()
                job.failed_competitors += 1
        db.commit()


def _check_scheduled_competitor_scrapes(db) -> None:
    """
    Check for competitors due for scheduled scraping.

    Creates a scheduled scrape job for due competitors.
    """
    due_competitors = CompetitorService.get_due_scheduled_competitors(db)

    if not due_competitors:
        return

    logger.info(f"Found {len(due_competitors)} competitors due for scheduled scrape")

    # Group by marketplace
    by_marketplace = {}
    for comp in due_competitors:
        mp = comp.marketplace
        if mp not in by_marketplace:
            by_marketplace[mp] = []
        by_marketplace[mp].append(comp)

    # Create a job for each marketplace
    for marketplace, competitors in by_marketplace.items():
        from ..competitors.schemas import ScrapeJobCreate as CompScrapeJobCreate

        job_data = CompScrapeJobCreate(
            job_name=f"Scheduled scan - {marketplace} - {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            marketplace=marketplace,
            competitor_ids=[c.id for c in competitors],
        )

        job = CompetitorService.create_scrape_job(db, job_data)
        job.job_type = "scheduled"
        db.commit()

        logger.info(
            f"Created scheduled competitor job {job.id} for {len(competitors)} "
            f"competitors in {marketplace}"
        )
