# =============================================================================
# SKU Domain - Pydantic Schemas
# =============================================================================
# Purpose: Request/response models for SKU endpoints
# Public API: SkuCreate, SkuUpdate, SkuResponse, SkuListResponse
# Dependencies: pydantic
# =============================================================================

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# ===== Request Schemas =====

class SkuCreate(BaseModel):
    """Schema for creating a new SKU."""

    sku_code: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None


class SkuUpdate(BaseModel):
    """Schema for updating an existing SKU."""

    sku_code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None


# ===== Response Schemas =====

class SkuResponse(BaseModel):
    """SKU response with basic info."""

    id: int
    sku_code: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SkuWithJobCountResponse(SkuResponse):
    """SKU response including job count."""

    job_count: int = 0


class SkuListResponse(BaseModel):
    """Paginated list of SKUs."""

    items: List[SkuWithJobCountResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class SkuSearchResult(BaseModel):
    """Simplified SKU for autocomplete search."""

    id: int
    sku_code: str

    class Config:
        from_attributes = True
