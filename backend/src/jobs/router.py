# =============================================================================
# Jobs Domain - API Router
# =============================================================================
# Purpose: REST API endpoints for scrape job management
# Public API: router
# Dependencies: fastapi, sqlalchemy, service, schemas
# =============================================================================

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..pagination import PaginationParams, get_pagination_params, create_paginated_response
from ..skus.service import SkuService
from .service import JobService
from .models import ScrapeJob
from .dependencies import valid_job, valid_job_for_cancel, valid_job_for_retry
from .schemas import (
    JobCreate,
    JobResponse,
    JobListItem,
    JobListResponse,
    JobDetailResponse,
    JobAsinResponse,
    AsinCheckRequest,
    AsinCheckResponse,
    AsinCheckResult,
)


router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


# ===== List Endpoints =====

@router.get("", response_model=JobListResponse)
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    sku_id: Optional[int] = Query(None, description="Filter by SKU"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db),
):
    """
    List all jobs with pagination and filters.

    Returns jobs ordered by creation date (newest first).
    """
    service = JobService(db)
    jobs, total = service.list_jobs(
        offset=pagination.offset,
        limit=pagination.limit,
        status=status,
        sku_id=sku_id,
    )

    # Build response items with SKU code
    items = []
    for job in jobs:
        sku_code = job.sku.sku_code if job.sku else None
        items.append(
            JobListItem(
                id=job.id,
                job_name=job.job_name,
                sku_code=sku_code,
                status=job.status,
                total_asins=job.total_asins,
                completed_asins=job.completed_asins,
                failed_asins=job.failed_asins,
                total_reviews=job.total_reviews,
                created_at=job.created_at,
                completed_at=job.completed_at,
            )
        )

    return create_paginated_response(items, total, pagination)


# ===== CRUD Endpoints =====

@router.post("", response_model=JobResponse, status_code=201)
async def create_job(
    data: JobCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new scrape job.

    Accepts a list of ASINs and job configuration.
    Creates new SKU if sku_code is provided and doesn't exist.
    """
    job_service = JobService(db)
    sku_service = SkuService(db)

    # Handle SKU
    sku_id = data.sku_id
    if data.sku_code and not sku_id:
        sku = sku_service.get_or_create(data.sku_code)
        sku_id = sku.id

    # Clean ASINs
    asins = [a.strip().upper() for a in data.asins if a.strip()]
    if not asins:
        raise HTTPException(status_code=400, detail="No valid ASINs provided")

    # Create job
    job = job_service.create_job(
        job_name=data.job_name,
        asins=asins,
        sku_id=sku_id,
        marketplace=data.marketplace,
        sort_by=data.sort_by,
        max_pages=data.max_pages,
        star_filters=data.star_filters,
        keyword_filter=data.keyword_filter,
        reviewer_type=data.reviewer_type,
        apify_delay_seconds=data.apify_delay_seconds,
    )

    return _build_job_response(job)


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(
    job: ScrapeJob = Depends(valid_job),
):
    """Get job details with ASIN breakdown."""
    response = _build_job_response(job)

    # Add ASIN details
    asins = [
        JobAsinResponse(
            id=a.id,
            asin=a.asin,
            product_title=a.product_title,
            status=a.status,
            reviews_found=a.reviews_found,
            error_message=a.error_message,
            started_at=a.started_at,
            completed_at=a.completed_at,
        )
        for a in job.asins
    ]

    return JobDetailResponse(**response.model_dump(), asins=asins)


@router.delete("/{job_id}", status_code=204)
async def delete_job(
    job: ScrapeJob = Depends(valid_job),
    db: Session = Depends(get_db),
):
    """Delete job and all associated data."""
    service = JobService(db)
    service.delete_job(job)


# ===== Job Actions =====

@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(
    job: ScrapeJob = Depends(valid_job_for_cancel),
    db: Session = Depends(get_db),
):
    """Cancel a queued or running job."""
    service = JobService(db)
    service.cancel_job(job)
    db.refresh(job)
    return _build_job_response(job)


@router.post("/{job_id}/retry-failed", response_model=JobResponse)
async def retry_failed_asins(
    job: ScrapeJob = Depends(valid_job_for_retry),
    db: Session = Depends(get_db),
):
    """
    Retry failed ASINs in a job.

    Resets failed ASINs to pending and sets job back to queued.
    """
    service = JobService(db)
    retry_count = service.retry_failed_asins(job.id)

    if retry_count == 0:
        raise HTTPException(status_code=400, detail="No failed ASINs to retry")

    # Set job back to queued
    job.status = "queued"
    job.completed_at = None
    job.error_message = None
    db.commit()
    db.refresh(job)

    return _build_job_response(job)


# ===== ASIN History =====

@router.post("/check-history", response_model=AsinCheckResponse)
async def check_asin_history(
    data: AsinCheckRequest,
    db: Session = Depends(get_db),
):
    """
    Check if ASINs have been scraped before.

    Returns history info for each ASIN.
    """
    service = JobService(db)
    results = service.check_asin_history(data.asins, data.marketplace)

    return AsinCheckResponse(
        results=[AsinCheckResult(**r) for r in results]
    )


# ===== Helper Functions =====

def _build_job_response(job: ScrapeJob) -> JobResponse:
    """Build JobResponse from ScrapeJob model."""
    sku_code = job.sku.sku_code if job.sku else None

    return JobResponse(
        id=job.id,
        job_name=job.job_name,
        sku_id=job.sku_id,
        sku_code=sku_code,
        status=job.status,
        marketplace=job.marketplace,
        sort_by=job.sort_by,
        max_pages=job.max_pages,
        star_filters=job.star_filters,
        keyword_filter=job.keyword_filter,
        reviewer_type=job.reviewer_type,
        total_asins=job.total_asins,
        completed_asins=job.completed_asins,
        failed_asins=job.failed_asins,
        total_reviews=job.total_reviews,
        apify_delay_seconds=job.apify_delay_seconds,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )
