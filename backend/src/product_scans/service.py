# =============================================================================
# Product Scans Domain - Business Logic
# =============================================================================
# Purpose: Service layer for product scan job operations
# Public API: ProductScanService
# Dependencies: sqlalchemy, models, channel_skus
# =============================================================================

from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_

from .models import ProductScanJob, ProductScanItem, JobStatus, ItemStatus
from ..channel_skus.models import ChannelSku
from ..channel_skus.service import ChannelSkuService
from ..skus.service import SkuService


class ProductScanService:
    """
    Service class for product scan job operations.

    Handles job creation, status updates, and result queries.
    """

    def __init__(self, db: Session):
        self.db = db

    # ===== Job Creation =====

    def create_job(
        self,
        job_name: str,
        marketplace: str,
        listings: List[dict],
    ) -> ProductScanJob:
        """
        Create a new product scan job with items.

        For each listing, creates or finds the parent SKU and Channel SKU,
        then creates a scan item.

        Args:
            job_name: User-provided job name
            marketplace: Amazon marketplace code
            listings: List of {sku_code, channel_sku_code, asin} dicts

        Returns:
            Created ProductScanJob
        """
        channel_sku_service = ChannelSkuService(self.db)
        sku_service = SkuService(self.db)

        # Create job
        job = ProductScanJob(
            job_name=job_name,
            marketplace=marketplace,
            status=JobStatus.QUEUED,
            total_listings=len(listings),
        )
        self.db.add(job)
        self.db.flush()  # Get job ID

        # Cache for parent SKUs to avoid repeated lookups
        sku_cache = {}

        # Create scan items
        for listing in listings:
            # Get or create parent SKU
            sku_code = listing.get("sku_code")
            sku_id = None
            if sku_code:
                if sku_code not in sku_cache:
                    sku = sku_service.get_or_create(sku_code)
                    sku_cache[sku_code] = sku.id
                sku_id = sku_cache[sku_code]

            # Get or create Channel SKU
            channel_sku = channel_sku_service.get_by_code_and_marketplace(
                listing["channel_sku_code"], marketplace
            )
            if not channel_sku:
                channel_sku = channel_sku_service.create(
                    channel_sku_code=listing["channel_sku_code"],
                    marketplace=marketplace,
                    current_asin=listing["asin"],
                    sku_id=sku_id,
                )
            elif sku_id and not channel_sku.sku_id:
                # Link existing Channel SKU to parent SKU if not already linked
                channel_sku.sku_id = sku_id

            item = ProductScanItem(
                job_id=job.id,
                channel_sku_id=channel_sku.id,
                input_asin=listing["asin"],
                status=ItemStatus.PENDING,
            )
            self.db.add(item)

        self.db.commit()
        self.db.refresh(job)
        return job

    def create_job_from_channel_skus(
        self,
        job_name: str,
        marketplace: str,
        channel_sku_ids: List[int],
    ) -> ProductScanJob:
        """
        Create a scan job from existing Channel SKU IDs.

        Args:
            job_name: User-provided job name
            marketplace: Amazon marketplace code
            channel_sku_ids: List of Channel SKU IDs to scan

        Returns:
            Created ProductScanJob
        """
        # Get Channel SKUs
        channel_skus = (
            self.db.query(ChannelSku)
            .filter(ChannelSku.id.in_(channel_sku_ids))
            .all()
        )

        if not channel_skus:
            raise ValueError("No valid Channel SKUs found")

        # Create job
        job = ProductScanJob(
            job_name=job_name,
            marketplace=marketplace,
            status=JobStatus.QUEUED,
            total_listings=len(channel_skus),
        )
        self.db.add(job)
        self.db.flush()

        # Create scan items
        for channel_sku in channel_skus:
            item = ProductScanItem(
                job_id=job.id,
                channel_sku_id=channel_sku.id,
                input_asin=channel_sku.current_asin,
                status=ItemStatus.PENDING,
            )
            self.db.add(item)

        self.db.commit()
        self.db.refresh(job)
        return job

    # ===== Job Queries =====

    def get_by_id(self, job_id: int) -> Optional[ProductScanJob]:
        """Get job by ID with items."""
        return (
            self.db.query(ProductScanJob)
            .filter(ProductScanJob.id == job_id)
            .first()
        )

    def list_jobs(
        self,
        offset: int = 0,
        limit: int = 50,
        status: Optional[JobStatus] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[ProductScanJob], int]:
        """
        List jobs with pagination and filters.

        Args:
            offset: Number to skip
            limit: Max to return
            status: Filter by status
            search: Search job name

        Returns:
            Tuple of (jobs list, total count)
        """
        query = self.db.query(ProductScanJob)

        if status:
            query = query.filter(ProductScanJob.status == status)

        if search:
            query = query.filter(ProductScanJob.job_name.ilike(f"%{search}%"))

        query = query.order_by(ProductScanJob.created_at.desc())
        total = query.count()
        items = query.offset(offset).limit(limit).all()

        return items, total

    def get_next_queued_job(self) -> Optional[ProductScanJob]:
        """Get the next queued job for processing."""
        return (
            self.db.query(ProductScanJob)
            .filter(ProductScanJob.status == JobStatus.QUEUED)
            .order_by(ProductScanJob.created_at)
            .first()
        )

    # ===== Item Queries =====

    def get_pending_items(
        self, job_id: int, limit: int = 50
    ) -> List[ProductScanItem]:
        """Get pending items for a job."""
        return (
            self.db.query(ProductScanItem)
            .options(joinedload(ProductScanItem.channel_sku))
            .filter(
                ProductScanItem.job_id == job_id,
                ProductScanItem.status == ItemStatus.PENDING,
            )
            .limit(limit)
            .all()
        )

    def get_job_items(
        self,
        job_id: int,
        offset: int = 0,
        limit: int = 50,
        status: Optional[ItemStatus] = None,
    ) -> Tuple[List[ProductScanItem], int]:
        """Get items for a job with pagination."""
        query = (
            self.db.query(ProductScanItem)
            .options(joinedload(ProductScanItem.channel_sku))
            .filter(ProductScanItem.job_id == job_id)
        )

        if status:
            query = query.filter(ProductScanItem.status == status)

        query = query.order_by(ProductScanItem.id)
        total = query.count()
        items = query.offset(offset).limit(limit).all()

        return items, total

    # ===== Status Updates =====

    def start_job(self, job: ProductScanJob) -> None:
        """Mark job as running."""
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        self.db.commit()

    def complete_job(self, job: ProductScanJob) -> None:
        """Mark job as completed or partial based on results."""
        # Count statuses
        completed = (
            self.db.query(func.count(ProductScanItem.id))
            .filter(
                ProductScanItem.job_id == job.id,
                ProductScanItem.status == ItemStatus.COMPLETED,
            )
            .scalar()
        )
        failed = (
            self.db.query(func.count(ProductScanItem.id))
            .filter(
                ProductScanItem.job_id == job.id,
                ProductScanItem.status == ItemStatus.FAILED,
            )
            .scalar()
        )

        job.completed_listings = completed or 0
        job.failed_listings = failed or 0
        job.completed_at = datetime.utcnow()

        if failed > 0 and completed > 0:
            job.status = JobStatus.PARTIAL
        elif failed > 0 and completed == 0:
            job.status = JobStatus.FAILED
        else:
            job.status = JobStatus.COMPLETED

        self.db.commit()

    def fail_job(self, job: ProductScanJob, error_message: str) -> None:
        """Mark job as failed with error."""
        job.status = JobStatus.FAILED
        job.error_message = error_message
        job.completed_at = datetime.utcnow()
        self.db.commit()

    def cancel_job(self, job: ProductScanJob) -> None:
        """Cancel a queued or running job."""
        if job.status not in [JobStatus.QUEUED, JobStatus.RUNNING]:
            raise ValueError(f"Cannot cancel job in {job.status} status")

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        self.db.commit()

    def mark_item_running(self, item: ProductScanItem) -> None:
        """Mark item as running."""
        item.status = ItemStatus.RUNNING
        item.started_at = datetime.utcnow()
        self.db.commit()

    def complete_item(
        self,
        item: ProductScanItem,
        rating: Optional[float],
        review_count: Optional[int],
        title: Optional[str],
        scraped_asin: Optional[str],
        raw_data: Optional[dict],
        apify_run_id: Optional[str] = None,
    ) -> None:
        """Mark item as completed with scraped data."""
        item.status = ItemStatus.COMPLETED
        item.scraped_rating = rating
        item.scraped_review_count = review_count
        item.scraped_title = title
        item.scraped_asin = scraped_asin
        item.raw_data = raw_data
        item.apify_run_id = apify_run_id
        item.completed_at = datetime.utcnow()
        self.db.commit()

    def fail_item(
        self,
        item: ProductScanItem,
        error_message: str,
        apify_run_id: Optional[str] = None,
    ) -> None:
        """Mark item as failed."""
        item.status = ItemStatus.FAILED
        item.error_message = error_message
        item.apify_run_id = apify_run_id
        item.completed_at = datetime.utcnow()
        self.db.commit()

    # ===== Retry Operations =====

    def retry_failed_items(self, job: ProductScanJob) -> int:
        """Reset failed items to pending for retry."""
        result = (
            self.db.query(ProductScanItem)
            .filter(
                ProductScanItem.job_id == job.id,
                ProductScanItem.status == ItemStatus.FAILED,
            )
            .update({
                ProductScanItem.status: ItemStatus.PENDING,
                ProductScanItem.error_message: None,
                ProductScanItem.started_at: None,
                ProductScanItem.completed_at: None,
            })
        )

        # Reset job status
        if result > 0:
            job.status = JobStatus.QUEUED
            job.completed_at = None

        self.db.commit()
        return result

    def get_real_time_progress(self, job_id: int) -> tuple[int, int]:
        """Get real-time completed/failed counts from item statuses."""
        completed = (
            self.db.query(func.count(ProductScanItem.id))
            .filter(
                ProductScanItem.job_id == job_id,
                ProductScanItem.status == ItemStatus.COMPLETED,
            )
            .scalar() or 0
        )
        failed = (
            self.db.query(func.count(ProductScanItem.id))
            .filter(
                ProductScanItem.job_id == job_id,
                ProductScanItem.status == ItemStatus.FAILED,
            )
            .scalar() or 0
        )
        return completed, failed

    # ===== Delete Operations =====

    def delete_job(self, job: ProductScanJob) -> None:
        """Delete job and all its items."""
        self.db.delete(job)
        self.db.commit()

    # ===== Statistics =====

    def get_job_summary(self, job_id: int) -> dict:
        """Get summary statistics for a job."""
        # Status counts
        status_counts = (
            self.db.query(
                ProductScanItem.status,
                func.count(ProductScanItem.id).label("count"),
            )
            .filter(ProductScanItem.job_id == job_id)
            .group_by(ProductScanItem.status)
            .all()
        )

        counts = {s.status.value: s.count for s in status_counts}

        # Average rating
        avg_rating = (
            self.db.query(func.avg(ProductScanItem.scraped_rating))
            .filter(
                ProductScanItem.job_id == job_id,
                ProductScanItem.scraped_rating.isnot(None),
            )
            .scalar()
        )

        # Total reviews
        total_reviews = (
            self.db.query(func.sum(ProductScanItem.scraped_review_count))
            .filter(
                ProductScanItem.job_id == job_id,
                ProductScanItem.scraped_review_count.isnot(None),
            )
            .scalar()
        )

        # ASIN changes count
        asin_changes = (
            self.db.query(func.count(ProductScanItem.id))
            .filter(
                ProductScanItem.job_id == job_id,
                ProductScanItem.scraped_asin.isnot(None),
                ProductScanItem.scraped_asin != ProductScanItem.input_asin,
            )
            .scalar()
        )

        return {
            "total_items": sum(counts.values()),
            "completed": counts.get("completed", 0),
            "failed": counts.get("failed", 0),
            "pending": counts.get("pending", 0),
            "running": counts.get("running", 0),
            "average_rating": float(avg_rating) if avg_rating else None,
            "total_reviews": total_reviews or 0,
            "asin_changes": asin_changes or 0,
        }

    def get_dashboard_stats(self) -> dict:
        """Get stats for dashboard."""
        # Jobs by status
        status_counts = (
            self.db.query(
                ProductScanJob.status,
                func.count(ProductScanJob.id).label("count"),
            )
            .group_by(ProductScanJob.status)
            .all()
        )

        # Total listings scanned
        total_scanned = (
            self.db.query(func.sum(ProductScanJob.completed_listings))
            .scalar()
        )

        # Recent jobs
        recent = (
            self.db.query(ProductScanJob)
            .order_by(ProductScanJob.created_at.desc())
            .limit(5)
            .all()
        )

        return {
            "total_jobs": sum(s.count for s in status_counts),
            "total_listings_scanned": total_scanned or 0,
            "jobs_by_status": {s.status.value: s.count for s in status_counts},
            "recent_jobs": recent,
        }
