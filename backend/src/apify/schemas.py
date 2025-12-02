# =============================================================================
# Apify Domain - Pydantic Schemas
# =============================================================================
# Purpose: Request/response models for Apify integration
# Public API: ApifyReviewInput, ApifyReviewResult
# Dependencies: pydantic
# =============================================================================

from typing import Optional, List
from pydantic import BaseModel
from enum import Enum


class StarFilter(str, Enum):
    """Valid star filter values for Apify actor."""
    ALL = "all_stars"
    FIVE = "five_star"
    FOUR = "four_star"
    THREE = "three_star"
    TWO = "two_star"
    ONE = "one_star"
    POSITIVE = "positive"
    CRITICAL = "critical"


class SortBy(str, Enum):
    """Valid sort options for reviews."""
    RECENT = "recent"
    HELPFUL = "helpful"


class ReviewerType(str, Enum):
    """Valid reviewer type filters."""
    ALL = "all_reviews"
    VERIFIED = "avp_only_reviews"


class ApifyReviewInput(BaseModel):
    """
    Input configuration for Apify reviews scraper.

    Matches the input schema of axesso_data~amazon-reviews-scraper.
    """

    productUrls: List[dict]  # [{"url": "..."}]
    maxReviews: int = 100
    sortBy: str = "recent"
    filterByKeyword: Optional[str] = None
    filterByStar: str = "all_stars"
    reviewerType: str = "all_reviews"


class ApifyReviewItem(BaseModel):
    """
    Single review item from Apify response.

    Maps to the actor's output schema.
    """

    reviewId: Optional[str] = None
    reviewTitle: Optional[str] = None
    reviewDescription: Optional[str] = None
    reviewRating: Optional[str] = None
    reviewDate: Optional[str] = None
    userName: Optional[str] = None
    isVerified: Optional[bool] = False
    helpfulCount: Optional[int] = 0
    productTitle: Optional[str] = None
    asin: Optional[str] = None


class ApifyActorType(str, Enum):
    """
    Supported Apify actor types.

    Extensible for future actors (product details, search results).
    """

    REVIEWS = "reviews"
    PRODUCT_DETAILS = "product_details"
    # SEARCH_RESULTS = "search_results"    # Future


# ===== Product Details Scraper Schemas =====


class ApifyProductInput(BaseModel):
    """
    Input configuration for Apify product details scraper.

    Matches the input schema of axesso_data~amazon-product-details-scraper.
    """

    urls: List[str]  # List of Amazon product URLs


class ApifyProductResult(BaseModel):
    """
    Single product result from Apify product details scraper.

    Maps to the actor's output schema.
    """

    statusCode: Optional[int] = None
    statusMessage: Optional[str] = None
    productRating: Optional[str] = None  # "4.5 out of 5 stars" - needs parsing
    countReview: Optional[int] = None
    asin: Optional[str] = None
    title: Optional[str] = None
    price: Optional[str] = None
    currency: Optional[str] = None
    url: Optional[str] = None
