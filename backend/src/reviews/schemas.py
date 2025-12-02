# =============================================================================
# Reviews Domain - Pydantic Schemas
# =============================================================================
# Purpose: Request/response models for review endpoints
# Public API: ReviewResponse, ReviewListResponse, FormattedReviewsResponse
# Dependencies: pydantic
# =============================================================================

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class ReviewResponse(BaseModel):
    """Full review response with all fields."""

    id: int
    job_asin_id: int
    asin: Optional[str] = None
    review_id: Optional[str]
    title: Optional[str]
    text: Optional[str]
    rating: Optional[str]
    date: Optional[str]
    user_name: Optional[str]
    verified: bool
    helpful_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    """Paginated list of reviews."""

    items: List[ReviewResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class FormattedReviewItem(BaseModel):
    """Single formatted review for copy output."""

    title: str
    text: str


class FormattedReviewsResponse(BaseModel):
    """
    Formatted reviews ready for copying.

    Output format:
        Title 1
        Review text 1

        Title 2
        Review text 2
    """

    reviews: List[FormattedReviewItem]
    total: int
    formatted_text: str  # Pre-formatted text for one-click copy


class ReviewStatsResponse(BaseModel):
    """Review statistics for a job."""

    total_reviews: int
    five_star: int = 0
    four_star: int = 0
    three_star: int = 0
    two_star: int = 0
    one_star: int = 0
    verified_count: int = 0
    average_rating: Optional[float] = None
