# =============================================================================
# Competitors Domain - Pydantic Schemas
# =============================================================================
# Purpose: Request/Response models for competitor API endpoints
# Public API: All schema classes
# Dependencies: pydantic
# =============================================================================

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Any
from enum import Enum

import json

from pydantic import BaseModel, Field, ConfigDict, field_validator


# =============================================================================
# Enums
# =============================================================================


class ScheduleType(str, Enum):
    NONE = "none"
    DAILY = "daily"
    EVERY_2_DAYS = "every_2_days"
    EVERY_3_DAYS = "every_3_days"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"


class ItemStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# Competitor Schemas
# =============================================================================


class CompetitorBase(BaseModel):
    """Base schema for competitor."""

    asin: str = Field(..., min_length=10, max_length=15)
    marketplace: str = Field(default="com", max_length=10)
    pack_size: Optional[int] = Field(default=1, ge=1)
    display_name: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = None


class CompetitorCreate(CompetitorBase):
    """Schema for creating a competitor."""

    sku_id: Optional[int] = None
    schedule: ScheduleType = ScheduleType.NONE


class CompetitorBulkCreate(BaseModel):
    """Schema for bulk creating competitors."""

    competitors: List[CompetitorCreate]


class CompetitorUpdate(BaseModel):
    """Schema for updating a competitor."""

    sku_id: Optional[int] = None
    pack_size: Optional[int] = Field(default=None, ge=1)
    display_name: Optional[str] = Field(default=None, max_length=255)
    schedule: Optional[ScheduleType] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class CompetitorScheduleUpdate(BaseModel):
    """Schema for updating competitor schedule."""

    schedule: ScheduleType


class CompetitorResponse(CompetitorBase):
    """Response schema for competitor."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sku_id: Optional[int] = None
    schedule: str
    next_scrape_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Nested data (optional, loaded when needed)
    sku_code: Optional[str] = None
    sku_display_name: Optional[str] = None


class CompetitorListResponse(BaseModel):
    """Paginated response for competitor list."""

    items: List[CompetitorResponse]
    total: int
    page: int
    per_page: int
    pages: int


# =============================================================================
# Competitor Data Schemas
# =============================================================================


class CompetitorDataResponse(BaseModel):
    """Response schema for competitor scraped data."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    competitor_id: int
    title: Optional[str] = None
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    price: Optional[Decimal] = None
    retail_price: Optional[Decimal] = None
    shipping_price: Optional[Decimal] = None
    currency: Optional[str] = None
    unit_price: Optional[Decimal] = None
    price_saving: Optional[str] = None
    rating: Optional[Decimal] = None
    review_count: Optional[int] = None
    past_sales: Optional[str] = None
    availability: Optional[str] = None
    sold_by: Optional[str] = None
    fulfilled_by: Optional[str] = None
    seller_id: Optional[str] = None
    is_prime: bool = False
    features: Optional[List[str]] = None
    product_description: Optional[str] = None
    main_image_url: Optional[str] = None
    images: Optional[List[Any]] = None
    videos: Optional[List[Any]] = None
    categories: Optional[List[Any]] = None
    variations: Optional[Any] = None
    variations_count: int = 0
    product_details: Optional[Any] = None
    review_insights: Optional[Any] = None
    scraped_at: datetime

    @field_validator(
        "features",
        "images",
        "videos",
        "categories",
        "variations",
        "product_details",
        "review_insights",
        mode="before",
    )
    @classmethod
    def parse_json_string(cls, v):
        """Parse JSON string to Python object if needed."""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return v
        return v


class CompetitorDetailResponse(CompetitorResponse):
    """Full competitor detail with scraped data."""

    data: Optional[CompetitorDataResponse] = None


# =============================================================================
# Price History Schemas
# =============================================================================


class PriceHistoryResponse(BaseModel):
    """Response schema for price history entry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    competitor_id: int
    price: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    shipping_price: Optional[Decimal] = None
    availability: Optional[str] = None
    rating: Optional[Decimal] = None
    review_count: Optional[int] = None
    scraped_at: datetime


class PriceHistoryListResponse(BaseModel):
    """Paginated response for price history."""

    items: List[PriceHistoryResponse]
    total: int
    page: int
    per_page: int


class PriceChangeResponse(BaseModel):
    """Response for price change display on dashboard."""

    competitor_id: int
    competitor_asin: str
    sku_code: Optional[str] = None
    old_price: Optional[Decimal] = None
    new_price: Optional[Decimal] = None
    currency: str = "USD"
    recorded_at: datetime


# =============================================================================
# Keyword Schemas
# =============================================================================


class KeywordBase(BaseModel):
    """Base schema for keyword."""

    keyword: str = Field(..., min_length=1, max_length=255)
    marketplace: str = Field(default="com", max_length=10)
    notes: Optional[str] = None


class KeywordCreate(KeywordBase):
    """Schema for creating a keyword."""

    sku_id: Optional[int] = None


class KeywordUpdate(BaseModel):
    """Schema for updating a keyword."""

    sku_id: Optional[int] = None
    keyword: Optional[str] = Field(default=None, min_length=1, max_length=255)
    marketplace: Optional[str] = Field(default=None, max_length=10)
    notes: Optional[str] = None


class KeywordResponse(KeywordBase):
    """Response schema for keyword."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sku_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    # Nested data
    sku_code: Optional[str] = None
    linked_channel_skus_count: int = 0
    linked_competitors_count: int = 0


class KeywordListResponse(BaseModel):
    """Paginated response for keyword list."""

    items: List[KeywordResponse]
    total: int
    page: int
    per_page: int
    pages: int


class KeywordDetailResponse(KeywordResponse):
    """Full keyword detail with linked items."""

    linked_channel_skus: List[Any] = []
    linked_competitors: List[Any] = []


# =============================================================================
# Scrape Job Schemas
# =============================================================================


class ScrapeJobCreate(BaseModel):
    """Schema for creating a competitor scrape job."""

    job_name: str = Field(..., min_length=1, max_length=255)
    marketplace: str = Field(default="com", max_length=10)
    competitor_ids: Optional[List[int]] = None
    sku_id: Optional[int] = None  # Alternative: scrape all competitors for this SKU


class ScrapeJobResponse(BaseModel):
    """Response schema for scrape job."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_name: str
    status: str
    job_type: str
    marketplace: str
    total_competitors: int
    completed_competitors: int
    failed_competitors: int
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ScrapeJobListResponse(BaseModel):
    """Paginated response for scrape job list."""

    items: List[ScrapeJobResponse]
    total: int
    page: int
    per_page: int
    pages: int


class ScrapeItemResponse(BaseModel):
    """Response schema for scrape item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int
    competitor_id: int
    input_asin: str
    status: str
    error_message: Optional[str] = None
    apify_run_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Nested data
    competitor_display_name: Optional[str] = None


class ScrapeJobDetailResponse(ScrapeJobResponse):
    """Full scrape job detail with items."""

    items: List[ScrapeItemResponse] = []


# =============================================================================
# Dashboard Stats Schemas
# =============================================================================


class DashboardStats(BaseModel):
    """Global dashboard statistics."""

    total_competitors: int = 0
    active_competitors: int = 0
    total_keywords: int = 0
    total_parent_skus: int = 0
    competitors_by_marketplace: dict = {}
    recent_price_changes: List[PriceChangeResponse] = []
    upcoming_scrapes: List[Any] = []


class ParentSkuStats(BaseModel):
    """Statistics for a single parent SKU."""

    sku_id: int
    sku_code: str
    display_name: Optional[str] = None
    total_competitors: int = 0
    total_keywords: int = 0
    total_channel_skus: int = 0
    avg_competitor_price: Optional[Decimal] = None
    min_competitor_price: Optional[Decimal] = None
    max_competitor_price: Optional[Decimal] = None
    avg_competitor_rating: Optional[Decimal] = None
    competitors: List[CompetitorResponse] = []
    keywords: List[KeywordResponse] = []


class ParentSkuListResponse(BaseModel):
    """Paginated response for parent SKU list with competitor stats."""

    items: List[ParentSkuStats]
    total: int
    page: int
    per_page: int
    pages: int


# =============================================================================
# Export Schemas
# =============================================================================


class PriceChangerExport(BaseModel):
    """Schema for price changer tool export."""

    asin: str
    marketplace: str
    competitor_name: Optional[str] = None
    parent_sku: Optional[str] = None
    price: Optional[Decimal] = None
    unit_price: Optional[Decimal] = None
    pack_size: int = 1
    rating: Optional[Decimal] = None
    review_count: Optional[int] = None
    availability: Optional[str] = None
    scraped_at: Optional[datetime] = None
