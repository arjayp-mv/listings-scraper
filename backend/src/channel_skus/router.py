# =============================================================================
# Channel SKUs Domain - API Router
# =============================================================================
# Purpose: REST API endpoints for Channel SKU management
# Public API: router
# Dependencies: fastapi, sqlalchemy, service, schemas
# =============================================================================

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import csv

from ..database import get_db
from ..pagination import PaginationParams, get_pagination_params, create_paginated_response
from .service import ChannelSkuService
from .schemas import (
    ChannelSkuCreate,
    ChannelSkuUpdate,
    ChannelSkuResponse,
    ChannelSkuWithSkuResponse,
    ChannelSkuListResponse,
    ChannelSkuSearchResult,
    BulkChannelSkuCreate,
    BulkCreateResult,
    AsinHistoryResponse,
    ChannelSkuAsinHistoryResponse,
    ScanHistoryEntry,
    ScanHistoryResponse,
)


router = APIRouter(prefix="/api/channel-skus", tags=["Channel SKUs"])


# ===== List & Search Endpoints =====


@router.get("", response_model=ChannelSkuListResponse)
async def list_channel_skus(
    search: Optional[str] = Query(None, description="Search code, ASIN, or title"),
    marketplace: Optional[str] = Query(None, description="Filter by marketplace"),
    sku_id: Optional[int] = Query(None, description="Filter by parent SKU ID"),
    sku_code: Optional[str] = Query(None, description="Filter by parent SKU code"),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    max_rating: Optional[float] = Query(None, ge=0, le=5),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db),
):
    """
    List Channel SKUs with pagination and filters.

    Supports searching by code, ASIN, or title, and filtering by
    marketplace, parent SKU (ID or code), and rating range.
    """
    service = ChannelSkuService(db)
    items, total = service.list_all(
        offset=pagination.offset,
        limit=pagination.limit,
        search=search,
        marketplace=marketplace,
        sku_id=sku_id,
        sku_code=sku_code,
        min_rating=min_rating,
        max_rating=max_rating,
    )

    # Transform to response with SKU code
    response_items = []
    for item in items:
        response_items.append(
            ChannelSkuWithSkuResponse(
                id=item.id,
                channel_sku_code=item.channel_sku_code,
                marketplace=item.marketplace,
                current_asin=item.current_asin,
                product_title=item.product_title,
                latest_rating=item.latest_rating,
                latest_review_count=item.latest_review_count,
                last_scraped_at=item.last_scraped_at,
                sku_id=item.sku_id,
                created_at=item.created_at,
                updated_at=item.updated_at,
                sku_code=item.sku.sku_code if item.sku else None,
            )
        )

    return create_paginated_response(response_items, total, pagination)


@router.get("/search")
async def search_channel_skus(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[ChannelSkuSearchResult]:
    """
    Search Channel SKUs for autocomplete.

    Returns simplified list matching code or ASIN.
    """
    service = ChannelSkuService(db)
    items = service.search(q, limit)
    return [ChannelSkuSearchResult.model_validate(item) for item in items]


@router.get("/export/csv")
async def export_channel_skus_csv(
    marketplace: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Export all Channel SKUs as CSV."""
    service = ChannelSkuService(db)
    items, _ = service.list_all(offset=0, limit=10000, marketplace=marketplace)

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Channel SKU",
        "Marketplace",
        "ASIN",
        "Product Title",
        "Rating",
        "Review Count",
        "Last Scraped",
        "Parent SKU",
    ])

    # Data rows
    for item in items:
        writer.writerow([
            item.channel_sku_code,
            item.marketplace,
            item.current_asin,
            item.product_title or "",
            str(item.latest_rating) if item.latest_rating else "",
            str(item.latest_review_count) if item.latest_review_count else "",
            item.last_scraped_at.isoformat() if item.last_scraped_at else "",
            item.sku.sku_code if item.sku else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=channel_skus.csv"},
    )


# ===== CRUD Endpoints =====


@router.post("", response_model=ChannelSkuResponse, status_code=201)
async def create_channel_sku(
    data: ChannelSkuCreate,
    db: Session = Depends(get_db),
):
    """Create a new Channel SKU."""
    service = ChannelSkuService(db)

    # Check for duplicate
    existing = service.get_by_code_and_marketplace(
        data.channel_sku_code, data.marketplace
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Channel SKU '{data.channel_sku_code}' already exists for marketplace '{data.marketplace}'",
        )

    # Resolve sku_code to sku_id (auto-create SKU if needed) - only if sku_code provided
    sku_id = None
    if data.sku_code:
        sku_id = service.get_or_create_sku(data.sku_code)

    channel_sku = service.create(
        channel_sku_code=data.channel_sku_code,
        marketplace=data.marketplace,
        current_asin=data.current_asin,
        sku_id=sku_id,
        product_title=data.product_title,
    )
    return ChannelSkuResponse.model_validate(channel_sku)


@router.post("/bulk", response_model=BulkCreateResult)
async def bulk_create_channel_skus(
    data: BulkChannelSkuCreate,
    db: Session = Depends(get_db),
):
    """
    Bulk create Channel SKUs.

    Skips duplicates and returns count of created/skipped items.
    """
    service = ChannelSkuService(db)
    items_dicts = [item.model_dump() for item in data.items]
    created, skipped, errors = service.bulk_create(items_dicts)

    return BulkCreateResult(created=created, skipped=skipped, errors=errors)


@router.get("/{channel_sku_id}", response_model=ChannelSkuWithSkuResponse)
async def get_channel_sku(
    channel_sku_id: int,
    db: Session = Depends(get_db),
):
    """Get Channel SKU by ID."""
    service = ChannelSkuService(db)
    channel_sku = service.get_by_id(channel_sku_id)

    if not channel_sku:
        raise HTTPException(status_code=404, detail="Channel SKU not found")

    return ChannelSkuWithSkuResponse(
        id=channel_sku.id,
        channel_sku_code=channel_sku.channel_sku_code,
        marketplace=channel_sku.marketplace,
        current_asin=channel_sku.current_asin,
        product_title=channel_sku.product_title,
        latest_rating=channel_sku.latest_rating,
        latest_review_count=channel_sku.latest_review_count,
        last_scraped_at=channel_sku.last_scraped_at,
        sku_id=channel_sku.sku_id,
        created_at=channel_sku.created_at,
        updated_at=channel_sku.updated_at,
        sku_code=channel_sku.sku.sku_code if channel_sku.sku else None,
    )


@router.put("/{channel_sku_id}", response_model=ChannelSkuResponse)
async def update_channel_sku(
    channel_sku_id: int,
    data: ChannelSkuUpdate,
    db: Session = Depends(get_db),
):
    """Update Channel SKU fields."""
    service = ChannelSkuService(db)
    channel_sku = service.get_by_id(channel_sku_id)

    if not channel_sku:
        raise HTTPException(status_code=404, detail="Channel SKU not found")

    # Check for duplicate if changing code/marketplace
    if data.channel_sku_code or data.marketplace:
        new_code = data.channel_sku_code or channel_sku.channel_sku_code
        new_mp = data.marketplace or channel_sku.marketplace
        existing = service.get_by_code_and_marketplace(new_code, new_mp)
        if existing and existing.id != channel_sku_id:
            raise HTTPException(
                status_code=400,
                detail=f"Channel SKU '{new_code}' already exists for marketplace '{new_mp}'",
            )

    updated = service.update(
        channel_sku,
        channel_sku_code=data.channel_sku_code,
        marketplace=data.marketplace,
        current_asin=data.current_asin,
        sku_id=data.sku_id,
        product_title=data.product_title,
    )
    return ChannelSkuResponse.model_validate(updated)


@router.delete("/{channel_sku_id}", status_code=204)
async def delete_channel_sku(
    channel_sku_id: int,
    db: Session = Depends(get_db),
):
    """Delete Channel SKU."""
    service = ChannelSkuService(db)
    channel_sku = service.get_by_id(channel_sku_id)

    if not channel_sku:
        raise HTTPException(status_code=404, detail="Channel SKU not found")

    service.delete(channel_sku)


# ===== History Endpoint =====


@router.get("/{channel_sku_id}/history", response_model=ChannelSkuAsinHistoryResponse)
async def get_channel_sku_history(
    channel_sku_id: int,
    db: Session = Depends(get_db),
):
    """Get Channel SKU with ASIN change history."""
    service = ChannelSkuService(db)
    channel_sku = service.get_by_id(channel_sku_id)

    if not channel_sku:
        raise HTTPException(status_code=404, detail="Channel SKU not found")

    history = service.get_asin_history(channel_sku_id)

    return ChannelSkuAsinHistoryResponse(
        channel_sku=ChannelSkuResponse.model_validate(channel_sku),
        history=[AsinHistoryResponse.model_validate(h) for h in history],
    )


@router.get("/{channel_sku_id}/scan-history", response_model=ScanHistoryResponse)
async def get_channel_sku_scan_history(
    channel_sku_id: int,
    db: Session = Depends(get_db),
):
    """Get Channel SKU with scan metrics history (rating/reviews over time)."""
    service = ChannelSkuService(db)
    channel_sku = service.get_by_id(channel_sku_id)

    if not channel_sku:
        raise HTTPException(status_code=404, detail="Channel SKU not found")

    history = service.get_scan_history(channel_sku_id)

    return ScanHistoryResponse(
        channel_sku=ChannelSkuResponse.model_validate(channel_sku),
        history=[ScanHistoryEntry(**h) for h in history],
    )


# ===== Stats Endpoint =====


@router.get("/stats/summary")
async def get_channel_sku_stats(
    db: Session = Depends(get_db),
):
    """Get Channel SKU statistics for dashboard."""
    service = ChannelSkuService(db)

    return {
        "total": service.get_total_count(),
        "by_marketplace": service.get_marketplace_counts(),
        "rating_distribution": service.get_rating_distribution(),
    }
