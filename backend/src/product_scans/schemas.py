# =============================================================================
# Product Scans Domain - Pydantic Schemas
# =============================================================================
# Purpose: Request/response models for product scan endpoints
# Public API: ProductScanJobCreate, ProductScanJobResponse, etc.
# Dependencies: pydantic
# =============================================================================

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from .models import JobStatus, ItemStatus


# ===== Request Schemas =====


class ProductScanListingInput(BaseModel):
    """Single listing input for product scan."""
    sku_code: str = Field(..., min_length=1, max_length=50, description="Parent SKU code")
    channel_sku_code: str = Field(..., min_length=1, max_length=100)
    asin: str = Field(..., min_length=10, max_length=15)


class ProductScanJobCreate(BaseModel):
    """Schema for creating a product scan job."""
    job_name: str = Field(..., min_length=1, max_length=255)
    marketplace: str = Field(default="com", max_length=10)
    listings: List[ProductScanListingInput] = Field(..., min_length=1, max_length=2000)


class RetryFailedRequest(BaseModel):
    """Request to retry failed items in a job."""
    pass  # No additional fields needed


# ===== Response Schemas =====


class ProductScanItemResponse(BaseModel):
    """Response for a single scan item."""
    id: int
    job_id: int
    channel_sku_id: int
    input_asin: str
    status: ItemStatus
    scraped_rating: Optional[Decimal]
    scraped_review_count: Optional[int]
    scraped_title: Optional[str]
    scraped_asin: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProductScanItemWithSkuResponse(ProductScanItemResponse):
    """Scan item with Channel SKU info."""
    channel_sku_code: str
    asin_changed: bool = False  # True if scraped_asin != input_asin


class ProductScanJobResponse(BaseModel):
    """Basic job response."""
    id: int
    job_name: str
    status: JobStatus
    marketplace: str
    total_listings: int
    completed_listings: int
    failed_listings: int
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProductScanJobDetailResponse(ProductScanJobResponse):
    """Job response with progress percentage."""
    progress_percent: float = 0.0


class ProductScanJobListResponse(BaseModel):
    """Paginated list of product scan jobs."""
    items: List[ProductScanJobDetailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class ProductScanJobResultsResponse(BaseModel):
    """Paginated results for a job."""
    items: List[ProductScanItemWithSkuResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    summary: "ProductScanSummary"


class ProductScanSummary(BaseModel):
    """Summary statistics for a job's results."""
    total_items: int
    completed: int
    failed: int
    pending: int
    average_rating: Optional[float]
    total_reviews: int
    asin_changes: int  # Count of items where scraped ASIN != input ASIN


# ===== Dashboard Schemas =====


class ProductScanDashboardStats(BaseModel):
    """Stats for dashboard."""
    total_jobs: int
    total_listings_scanned: int
    jobs_by_status: dict
    recent_jobs: List[ProductScanJobResponse]
