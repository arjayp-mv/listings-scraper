# =============================================================================
# Jobs Domain - Business Logic
# =============================================================================
# Purpose: Service layer for scrape job operations
# Public API: JobService
# Dependencies: sqlalchemy, models, schemas
# =============================================================================

import json
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from .models import ScrapeJob, JobAsin
from ..skus.models import Sku
from ..reviews.models import AsinHistory


class JobService:
    """
    Service class for scrape job business logic.

    Handles job creation, status management, and queries.
    """

    def __init__(self, db: Session):
        self.db = db

    # ===== Job Creation =====

    def create_job(
        self,
        job_name: str,
        asins: List[str],
        sku_id: Optional[int] = None,
        marketplace: str = "com",
        sort_by: str = "recent",
        max_pages: int = 10,
        star_filters: Optional[List[str]] = None,
        keyword_filter: Optional[str] = None,
        reviewer_type: str = "all_reviews",
        apify_delay_seconds: int = 10,
    ) -> ScrapeJob:
        """
        Create a new scrape job with ASINs.

        Args:
            job_name: User-provided job name
            asins: List of ASIN codes to scrape
            sku_id: Optional SKU reference
            marketplace: Amazon domain
            sort_by: Sort order for reviews
            max_pages: Max pages per ASIN
            star_filters: Star rating filters
            keyword_filter: Optional keyword filter
            reviewer_type: Reviewer type filter
            apify_delay_seconds: Delay between API calls

        Returns:
            Created ScrapeJob instance
        """
        # Default star filters if not provided
        if star_filters is None:
            star_filters = ["five_star", "four_star"]

        # Create job
        job = ScrapeJob(
            job_name=job_name,
            sku_id=sku_id,
            marketplace=marketplace,
            sort_by=sort_by,
            max_pages=max_pages,
            star_filters=star_filters,
            keyword_filter=keyword_filter,
            reviewer_type=reviewer_type,
            apify_delay_seconds=apify_delay_seconds,
            total_asins=len(asins),
            status="queued",
        )
        self.db.add(job)
        self.db.flush()  # Get job.id

        # Create job ASINs
        for asin in asins:
            job_asin = JobAsin(
                job_id=job.id,
                asin=asin.strip().upper(),
                status="pending",
            )
            self.db.add(job_asin)

        self.db.commit()
        self.db.refresh(job)
        return job

    # ===== Job Queries =====

    def get_by_id(self, job_id: int) -> Optional[ScrapeJob]:
        """Get job by ID."""
        return self.db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()

    def list_jobs(
        self,
        offset: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        sku_id: Optional[int] = None,
    ) -> tuple[List[ScrapeJob], int]:
        """
        List jobs with filters and pagination.

        Returns:
            Tuple of (job list, total count)
        """
        query = self.db.query(ScrapeJob)

        if status:
            query = query.filter(ScrapeJob.status == status)
        if sku_id:
            query = query.filter(ScrapeJob.sku_id == sku_id)

        query = query.order_by(desc(ScrapeJob.created_at))

        total = query.count()
        items = query.offset(offset).limit(limit).all()
        return items, total

    def get_queued_job(self) -> Optional[ScrapeJob]:
        """Get oldest queued job for processing."""
        return (
            self.db.query(ScrapeJob)
            .filter(ScrapeJob.status == "queued")
            .order_by(ScrapeJob.created_at)
            .first()
        )

    # ===== Job Status Management =====

    def start_job(self, job: ScrapeJob) -> None:
        """Mark job as running."""
        job.status = "running"
        job.started_at = datetime.utcnow()
        self.db.commit()

    def complete_job(self, job: ScrapeJob, partial: bool = False) -> None:
        """Mark job as completed or partial."""
        job.status = "partial" if partial else "completed"
        job.completed_at = datetime.utcnow()
        self.db.commit()

    def fail_job(self, job: ScrapeJob, error_message: str) -> None:
        """Mark job as failed."""
        job.status = "failed"
        job.error_message = error_message
        job.completed_at = datetime.utcnow()
        self.db.commit()

    def cancel_job(self, job: ScrapeJob) -> None:
        """Cancel a job."""
        job.status = "cancelled"
        job.completed_at = datetime.utcnow()
        self.db.commit()

    def sync_job_stats(self, job: ScrapeJob) -> None:
        """
        Sync job statistics from job_asin records.

        Uses database aggregation per best practices.
        """
        stats = (
            self.db.query(
                func.count(JobAsin.id).label("total"),
                func.sum(func.if_(JobAsin.status == "completed", 1, 0)).label("completed"),
                func.sum(func.if_(JobAsin.status == "failed", 1, 0)).label("failed"),
                func.sum(JobAsin.reviews_found).label("reviews"),
            )
            .filter(JobAsin.job_id == job.id)
            .first()
        )

        job.total_asins = stats.total or 0
        job.completed_asins = int(stats.completed or 0)
        job.failed_asins = int(stats.failed or 0)
        job.total_reviews = int(stats.reviews or 0)
        self.db.commit()

    def delete_job(self, job: ScrapeJob) -> None:
        """Delete job and all associated data."""
        self.db.delete(job)
        self.db.commit()

    # ===== ASIN Operations =====

    def get_pending_asin(self, job_id: int) -> Optional[JobAsin]:
        """Get next pending ASIN for a job."""
        return (
            self.db.query(JobAsin)
            .filter(JobAsin.job_id == job_id, JobAsin.status == "pending")
            .first()
        )

    def get_failed_asins(self, job_id: int) -> List[JobAsin]:
        """Get all failed ASINs for a job."""
        return (
            self.db.query(JobAsin)
            .filter(JobAsin.job_id == job_id, JobAsin.status == "failed")
            .all()
        )

    def retry_failed_asins(self, job_id: int) -> int:
        """
        Reset failed ASINs to pending for retry.

        Returns count of ASINs reset.
        """
        result = (
            self.db.query(JobAsin)
            .filter(JobAsin.job_id == job_id, JobAsin.status == "failed")
            .update({"status": "pending", "error_message": None})
        )
        self.db.commit()
        return result

    # ===== ASIN History =====

    def check_asin_history(
        self,
        asins: List[str],
        marketplace: str,
    ) -> List[dict]:
        """
        Check if ASINs have been scraped before.

        Returns list of dicts with history info.
        """
        results = []
        for asin in asins:
            asin_upper = asin.strip().upper()
            history = (
                self.db.query(AsinHistory)
                .filter(
                    AsinHistory.asin == asin_upper,
                    AsinHistory.marketplace == marketplace,
                )
                .first()
            )

            results.append({
                "asin": asin_upper,
                "previously_scraped": history is not None,
                "last_scraped_at": history.last_scraped_at if history else None,
                "last_job_id": history.last_scraped_job_id if history else None,
            })

        return results

    def update_asin_history(
        self,
        asin: str,
        marketplace: str,
        job_id: int,
    ) -> None:
        """Update ASIN history after successful scrape."""
        history = (
            self.db.query(AsinHistory)
            .filter(
                AsinHistory.asin == asin,
                AsinHistory.marketplace == marketplace,
            )
            .first()
        )

        if history:
            history.last_scraped_job_id = job_id
            history.last_scraped_at = datetime.utcnow()
            history.total_scrapes += 1
        else:
            history = AsinHistory(
                asin=asin,
                marketplace=marketplace,
                last_scraped_job_id=job_id,
                last_scraped_at=datetime.utcnow(),
                total_scrapes=1,
            )
            self.db.add(history)

        self.db.commit()
