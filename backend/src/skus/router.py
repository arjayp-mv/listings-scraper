# =============================================================================
# SKU Domain - API Router
# =============================================================================
# Purpose: REST API endpoints for SKU management
# Public API: router
# Dependencies: fastapi, sqlalchemy, service, schemas
# =============================================================================

from typing import Optional
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..pagination import PaginationParams, get_pagination_params, create_paginated_response
from ..reviews.service import ReviewService
from ..reviews.schemas import (
    ReviewResponse,
    ReviewListResponse,
    FormattedReviewsResponse,
    ReviewStatsResponse,
)
from .service import SkuService
from .schemas import (
    SkuCreate,
    SkuUpdate,
    SkuResponse,
    SkuWithJobCountResponse,
    SkuListResponse,
    SkuSearchResult,
    SkuWithChannelSkuStats,
    SkuWithChannelSkuStatsListResponse,
)


router = APIRouter(prefix="/api/skus", tags=["SKUs"])


# ===== List Endpoints =====


@router.get("/with-channel-sku-stats", response_model=SkuWithChannelSkuStatsListResponse)
async def list_skus_with_channel_sku_stats(
    search: Optional[str] = Query(None, description="Search by SKU code"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db),
):
    """
    List SKUs with aggregated Channel SKU statistics.

    Returns SKUs ordered by sku_code with channel_sku_count, avg_rating,
    total_reviews, and last_scraped_at from their linked Channel SKUs.
    """
    service = SkuService(db)
    items, total = service.list_with_channel_sku_stats(
        offset=pagination.offset,
        limit=pagination.limit,
        search=search,
    )

    response_items = [SkuWithChannelSkuStats(**item) for item in items]
    return create_paginated_response(response_items, total, pagination)


@router.get("", response_model=SkuListResponse)
async def list_skus(
    search: Optional[str] = Query(None, description="Search by SKU code"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db),
):
    """
    List all SKUs with pagination and optional search.

    Returns SKUs ordered by sku_code with job counts.
    """
    service = SkuService(db)
    skus, total = service.list_all(
        offset=pagination.offset,
        limit=pagination.limit,
        search=search,
    )

    # Add job counts
    items = []
    for sku in skus:
        job_count = service.get_job_count(sku.id)
        items.append(
            SkuWithJobCountResponse(
                id=sku.id,
                sku_code=sku.sku_code,
                description=sku.description,
                created_at=sku.created_at,
                updated_at=sku.updated_at,
                job_count=job_count,
            )
        )

    return create_paginated_response(items, total, pagination)


@router.get("/search")
async def search_skus(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[SkuSearchResult]:
    """
    Search SKUs for autocomplete.

    Returns simplified SKU list matching the query.
    """
    service = SkuService(db)
    skus = service.search(q, limit)
    return [SkuSearchResult.model_validate(s) for s in skus]


# ===== CRUD Endpoints =====

@router.post("", response_model=SkuResponse, status_code=201)
async def create_sku(
    data: SkuCreate,
    db: Session = Depends(get_db),
):
    """Create a new SKU."""
    service = SkuService(db)

    # Check for duplicate
    existing = service.get_by_code(data.sku_code)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"SKU with code '{data.sku_code}' already exists",
        )

    sku = service.create(data.sku_code, data.description)
    return SkuResponse.model_validate(sku)


@router.get("/{sku_id}", response_model=SkuWithJobCountResponse)
async def get_sku(
    sku_id: int,
    db: Session = Depends(get_db),
):
    """Get SKU by ID with job count."""
    service = SkuService(db)
    sku = service.get_by_id(sku_id)

    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")

    job_count = service.get_job_count(sku.id)
    return SkuWithJobCountResponse(
        id=sku.id,
        sku_code=sku.sku_code,
        description=sku.description,
        created_at=sku.created_at,
        updated_at=sku.updated_at,
        job_count=job_count,
    )


@router.put("/{sku_id}", response_model=SkuResponse)
async def update_sku(
    sku_id: int,
    data: SkuUpdate,
    db: Session = Depends(get_db),
):
    """Update SKU fields."""
    service = SkuService(db)
    sku = service.get_by_id(sku_id)

    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")

    # Check for duplicate code if changing
    if data.sku_code and data.sku_code != sku.sku_code:
        existing = service.get_by_code(data.sku_code)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"SKU with code '{data.sku_code}' already exists",
            )

    updated = service.update(sku, data.sku_code, data.description)
    return SkuResponse.model_validate(updated)


@router.delete("/{sku_id}", status_code=204)
async def delete_sku(
    sku_id: int,
    db: Session = Depends(get_db),
):
    """Delete SKU."""
    service = SkuService(db)
    sku = service.get_by_id(sku_id)

    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")

    service.delete(sku)


# ===== SKU Reviews Endpoints =====

@router.get("/{sku_id}/reviews", response_model=ReviewListResponse)
async def list_sku_reviews(
    sku_id: int,
    search: Optional[str] = Query(None, description="Search in title/text"),
    rating: Optional[str] = Query(None, description="Filter by rating"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db),
):
    """
    List reviews for a SKU (across all its jobs).

    Supports search, rating filter, and pagination.
    """
    sku_service = SkuService(db)
    sku = sku_service.get_by_id(sku_id)
    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")

    review_service = ReviewService(db)
    reviews, total = review_service.get_reviews_for_sku(
        sku_id=sku_id,
        offset=pagination.offset,
        limit=pagination.limit,
        search=search,
        rating=rating,
    )

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


@router.get("/{sku_id}/reviews/formatted", response_model=FormattedReviewsResponse)
async def get_sku_formatted_reviews(
    sku_id: int,
    search: Optional[str] = Query(None, description="Search in title/text"),
    rating: Optional[str] = Query(None, description="Filter by rating"),
    db: Session = Depends(get_db),
):
    """
    Get SKU reviews formatted for copy/paste.

    Returns reviews in Title + Text format ready for AI tools.
    """
    sku_service = SkuService(db)
    sku = sku_service.get_by_id(sku_id)
    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")

    review_service = ReviewService(db)
    result = review_service.get_formatted_reviews_for_sku(
        sku_id=sku_id,
        search=search,
        rating=rating,
    )

    return FormattedReviewsResponse(**result)


@router.get("/{sku_id}/reviews/stats", response_model=ReviewStatsResponse)
async def get_sku_review_stats(
    sku_id: int,
    db: Session = Depends(get_db),
):
    """Get review statistics for a SKU."""
    sku_service = SkuService(db)
    sku = sku_service.get_by_id(sku_id)
    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")

    review_service = ReviewService(db)
    stats = review_service.get_review_stats_for_sku(sku_id)
    return ReviewStatsResponse(**stats)


@router.get("/{sku_id}/reviews/export/excel")
async def export_sku_reviews_excel(
    sku_id: int,
    db: Session = Depends(get_db),
):
    """Export all SKU reviews as Excel file."""
    from openpyxl import Workbook

    sku_service = SkuService(db)
    sku = sku_service.get_by_id(sku_id)
    if not sku:
        raise HTTPException(status_code=404, detail="SKU not found")

    review_service = ReviewService(db)
    reviews = review_service.get_all_reviews_for_sku(sku_id)

    wb = Workbook()
    ws = wb.active
    ws.title = "Reviews"

    headers = [
        "ASIN", "Review ID", "Title", "Text", "Rating",
        "Date", "User Name", "Verified", "Helpful Count"
    ]
    ws.append(headers)

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

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in sku.sku_code)
    filename = f"{safe_name}_reviews.xlsx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
