# =============================================================================
# Channel SKUs Domain - Pydantic Schemas
# =============================================================================
# Purpose: Request/response models for Channel SKU endpoints
# Public API: ChannelSkuCreate, ChannelSkuResponse, etc.
# Dependencies: pydantic
# =============================================================================

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


# ===== Request Schemas =====


class ChannelSkuCreate(BaseModel):
    """Schema for creating a new Channel SKU."""

    channel_sku_code: str = Field(..., min_length=1, max_length=100)
    marketplace: str = Field(default="com", max_length=10)
    current_asin: str = Field(..., min_length=10, max_length=15)
    sku_code: Optional[str] = Field(None, max_length=100, description="Optional parent SKU code")
    sku_id: Optional[int] = None  # Will be resolved from sku_code if provided
    product_title: Optional[str] = None


class ChannelSkuUpdate(BaseModel):
    """Schema for updating a Channel SKU."""

    channel_sku_code: Optional[str] = Field(None, min_length=1, max_length=100)
    marketplace: Optional[str] = Field(None, max_length=10)
    current_asin: Optional[str] = Field(None, min_length=10, max_length=15)
    sku_id: Optional[int] = None
    product_title: Optional[str] = None


class BulkChannelSkuCreate(BaseModel):
    """Schema for bulk creating Channel SKUs."""

    items: List[ChannelSkuCreate] = Field(..., min_length=1, max_length=500)


# ===== Response Schemas =====


class ChannelSkuResponse(BaseModel):
    """Basic Channel SKU response."""

    id: int
    channel_sku_code: str
    marketplace: str
    current_asin: str
    product_title: Optional[str]
    latest_rating: Optional[Decimal]
    latest_review_count: Optional[int]
    last_scraped_at: Optional[datetime]
    sku_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChannelSkuWithSkuResponse(ChannelSkuResponse):
    """Channel SKU response including parent SKU info."""

    sku_code: Optional[str] = None


class ChannelSkuListResponse(BaseModel):
    """Paginated list of Channel SKUs."""

    items: List[ChannelSkuWithSkuResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class ChannelSkuSearchResult(BaseModel):
    """Simplified Channel SKU for autocomplete search."""

    id: int
    channel_sku_code: str
    current_asin: str
    marketplace: str

    class Config:
        from_attributes = True


# ===== ASIN History Schemas =====


class AsinHistoryResponse(BaseModel):
    """ASIN change history entry."""

    id: int
    asin: str
    changed_at: datetime
    changed_by_job_id: Optional[int]

    class Config:
        from_attributes = True


class ChannelSkuAsinHistoryResponse(BaseModel):
    """Channel SKU with full ASIN history."""

    channel_sku: ChannelSkuResponse
    history: List[AsinHistoryResponse]


# ===== Bulk Operation Schemas =====


class BulkCreateResult(BaseModel):
    """Result of bulk create operation."""

    created: int
    skipped: int
    errors: List[str]


class BulkScanRequest(BaseModel):
    """Request to queue selected Channel SKUs for scanning."""

    channel_sku_ids: List[int] = Field(..., min_length=1, max_length=500)
    marketplace: Optional[str] = None  # Override marketplace if needed


# ===== Scan History Schemas =====


class ScanHistoryEntry(BaseModel):
    """A scan history entry showing rating/review changes over time."""

    job_id: int
    job_name: str
    scraped_at: Optional[datetime]
    rating: Optional[Decimal]
    review_count: Optional[int]
    scraped_asin: Optional[str]


class ScanHistoryResponse(BaseModel):
    """Scan history for a Channel SKU."""

    channel_sku: ChannelSkuResponse
    history: List[ScanHistoryEntry]


# ===== Export Schemas =====


class ChannelSkuExportRow(BaseModel):
    """Row format for Channel SKU export."""

    channel_sku_code: str
    marketplace: str
    current_asin: str
    product_title: Optional[str]
    latest_rating: Optional[Decimal]
    latest_review_count: Optional[int]
    last_scraped_at: Optional[datetime]
    sku_code: Optional[str]
