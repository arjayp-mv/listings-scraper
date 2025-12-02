# =============================================================================
# SKU Domain - API Router
# =============================================================================
# Purpose: REST API endpoints for SKU management
# Public API: router
# Dependencies: fastapi, sqlalchemy, service, schemas
# =============================================================================

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..pagination import PaginationParams, get_pagination_params, create_paginated_response
from .service import SkuService
from .schemas import (
    SkuCreate,
    SkuUpdate,
    SkuResponse,
    SkuWithJobCountResponse,
    SkuListResponse,
    SkuSearchResult,
)


router = APIRouter(prefix="/api/skus", tags=["SKUs"])


# ===== List Endpoints =====

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
