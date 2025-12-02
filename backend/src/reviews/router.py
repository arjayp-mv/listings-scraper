# =============================================================================
# Reviews Domain - API Router
# =============================================================================
# Purpose: REST API endpoints for review data access
# Public API: router
# Dependencies: fastapi, sqlalchemy, service, schemas
# =============================================================================

from typing import Optional
from io import BytesIO
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..pagination import PaginationParams, get_pagination_params, create_paginated_response
from ..jobs.models import ScrapeJob, JobAsin
from ..jobs.dependencies import valid_job
from .service import ReviewService
from .schemas import (
    ReviewResponse,
    ReviewListResponse,
    FormattedReviewsResponse,
    ReviewStatsResponse,
)


router = APIRouter(prefix="/api/jobs/{job_id}/reviews", tags=["Reviews"])


# ===== Review List =====

@router.get("", response_model=ReviewListResponse)
async def list_reviews(
    job: ScrapeJob = Depends(valid_job),
    search: Optional[str] = Query(None, description="Search in title/text"),
    rating: Optional[str] = Query(None, description="Filter by rating"),
    asin: Optional[str] = Query(None, description="Filter by ASIN"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db),
):
    """
    List reviews for a job with filters and pagination.

    Supports search, rating filter, and ASIN filter.
    """
    service = ReviewService(db)
    reviews, total = service.get_reviews_for_job(
        job_id=job.id,
        offset=pagination.offset,
        limit=pagination.limit,
        search=search,
        rating=rating,
        asin=asin,
    )

    # Build response with ASIN info
    items = []
    for review in reviews:
        items.append(
            ReviewResponse(
                id=review.id,
                job_asin_id=review.job_asin_id,
                asin=review.job_asin.asin,
                review_id=review.review_id,
                title=review.title,
                text=review.text,
                rating=review.rating,
                date=review.date,
                user_name=review.user_name,
                verified=review.verified,
                helpful_count=review.helpful_count,
                created_at=review.created_at,
            )
        )

    return create_paginated_response(items, total, pagination)


# ===== Formatted Output =====

@router.get("/formatted", response_model=FormattedReviewsResponse)
async def get_formatted_reviews(
    job: ScrapeJob = Depends(valid_job),
    search: Optional[str] = Query(None, description="Search in title/text"),
    rating: Optional[str] = Query(None, description="Filter by rating"),
    db: Session = Depends(get_db),
):
    """
    Get reviews formatted for copy/paste.

    Returns reviews in Title + Text format ready for AI tools.
    """
    service = ReviewService(db)
    result = service.get_formatted_reviews(
        job_id=job.id,
        search=search,
        rating=rating,
    )

    return FormattedReviewsResponse(**result)


# ===== Statistics =====

@router.get("/stats", response_model=ReviewStatsResponse)
async def get_review_stats(
    job: ScrapeJob = Depends(valid_job),
    db: Session = Depends(get_db),
):
    """Get review statistics for a job."""
    service = ReviewService(db)
    stats = service.get_review_stats(job.id)
    return ReviewStatsResponse(**stats)


# ===== Export =====

@router.get("/export/json")
async def export_reviews_json(
    job: ScrapeJob = Depends(valid_job),
    db: Session = Depends(get_db),
):
    """Export all reviews as JSON."""
    service = ReviewService(db)
    reviews = service.get_all_reviews_for_job(job.id)

    # Build export data
    export_data = []
    for review in reviews:
        export_data.append({
            "asin": review.job_asin.asin,
            "review_id": review.review_id,
            "title": review.title,
            "text": review.text,
            "rating": review.rating,
            "date": review.date,
            "user_name": review.user_name,
            "verified": review.verified,
            "helpful_count": review.helpful_count,
        })

    return export_data


@router.get("/export/excel")
async def export_reviews_excel(
    job: ScrapeJob = Depends(valid_job),
    db: Session = Depends(get_db),
):
    """Export all reviews as Excel file."""
    from openpyxl import Workbook

    service = ReviewService(db)
    reviews = service.get_all_reviews_for_job(job.id)

    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Reviews"

    # Header row
    headers = [
        "ASIN", "Review ID", "Title", "Text", "Rating",
        "Date", "User Name", "Verified", "Helpful Count"
    ]
    ws.append(headers)

    # Data rows
    for review in reviews:
        ws.append([
            review.job_asin.asin,
            review.review_id,
            review.title,
            review.text,
            review.rating,
            review.date,
            review.user_name,
            "Yes" if review.verified else "No",
            review.helpful_count,
        ])

    # Save to buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    # Clean filename
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in job.job_name)
    filename = f"{safe_name}_reviews.xlsx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
