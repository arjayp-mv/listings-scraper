# =============================================================================
# Jobs Domain - Pydantic Schemas
# =============================================================================
# Purpose: Request/response models for job endpoints
# Public API: JobCreate, JobResponse, JobListResponse, JobAsinResponse
# Dependencies: pydantic
# =============================================================================

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# ===== Request Schemas =====

class JobCreate(BaseModel):
    """
    Schema for creating a new scrape job.

    Matches the form fields from the New Scrape page.
    """

    job_name: str = Field(..., min_length=1, max_length=255)
    sku_id: Optional[int] = None
    sku_code: Optional[str] = None  # Create new SKU if provided
    asins: List[str] = Field(..., min_items=1)
    marketplace: str = Field(default="com", max_length=10)
    sort_by: str = Field(default="recent", max_length=20)
    max_pages: int = Field(default=10, ge=1, le=20)
    star_filters: List[str] = Field(default=["five_star", "four_star"])
    keyword_filter: Optional[str] = Field(None, max_length=255)
    reviewer_type: str = Field(default="all_reviews", max_length=20)
    apify_delay_seconds: int = Field(default=10, ge=0, le=60)


# ===== Response Schemas =====

class JobAsinResponse(BaseModel):
    """Response for individual ASIN within a job."""

    id: int
    asin: str
    product_title: Optional[str]
    status: str
    reviews_found: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class JobResponse(BaseModel):
    """Full job response with all details."""

    id: int
    job_name: str
    sku_id: Optional[int]
    sku_code: Optional[str] = None
    status: str
    marketplace: str
    sort_by: str
    max_pages: int
    star_filters: Optional[List[str]]
    keyword_filter: Optional[str]
    reviewer_type: str
    total_asins: int
    completed_asins: int
    failed_asins: int
    total_reviews: int
    apify_delay_seconds: int
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class JobListItem(BaseModel):
    """Simplified job item for list view."""

    id: int
    job_name: str
    sku_code: Optional[str] = None
    status: str
    total_asins: int
    completed_asins: int
    failed_asins: int
    total_reviews: int
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Paginated list of jobs."""

    items: List[JobListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class JobDetailResponse(JobResponse):
    """Job response with ASIN details."""

    asins: List[JobAsinResponse] = []


# ===== Utility Schemas =====

class AsinCheckRequest(BaseModel):
    """Request to check if ASINs have been scraped before."""

    asins: List[str]
    marketplace: str = "com"


class AsinCheckResult(BaseModel):
    """Result for single ASIN history check."""

    asin: str
    previously_scraped: bool
    last_scraped_at: Optional[datetime] = None
    last_job_id: Optional[int] = None


class AsinCheckResponse(BaseModel):
    """Response for ASIN history check."""

    results: List[AsinCheckResult]
