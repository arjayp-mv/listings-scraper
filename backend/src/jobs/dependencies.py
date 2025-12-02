# =============================================================================
# Jobs Domain - Route Dependencies
# =============================================================================
# Purpose: FastAPI dependencies for job validation
# Public API: valid_job, valid_job_for_cancel
# Dependencies: fastapi, sqlalchemy, models
# =============================================================================

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from .models import ScrapeJob


async def valid_job(
    job_id: int,
    db: Session = Depends(get_db),
) -> ScrapeJob:
    """
    Dependency that validates job exists.

    Raises 404 if job not found.
    """
    job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


async def valid_job_for_cancel(
    job: ScrapeJob = Depends(valid_job),
) -> ScrapeJob:
    """
    Dependency that validates job can be cancelled.

    Only queued or running jobs can be cancelled.
    """
    if job.status not in ("queued", "running"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job with status '{job.status}'",
        )
    return job


async def valid_job_for_retry(
    job: ScrapeJob = Depends(valid_job),
) -> ScrapeJob:
    """
    Dependency that validates job can have failed ASINs retried.

    Only completed, partial, or failed jobs can be retried.
    """
    if job.status not in ("completed", "partial", "failed"):
        raise HTTPException(
            status_code=400,
            detail="Can only retry failed ASINs on completed/partial/failed jobs",
        )
    return job
