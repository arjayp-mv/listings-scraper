# =============================================================================
# Apify Domain - API Client
# =============================================================================
# Purpose: Wrapper for Apify API calls to scrape Amazon reviews
# Public API: ApifyService
# Dependencies: apify-client, config, schemas, exceptions
# =============================================================================

import asyncio
import logging
from typing import List, Optional

from apify_client import ApifyClient

from ..config import settings
from .schemas import ApifyActorType, StarFilter, SortBy, ReviewerType
from .exceptions import ApifyError, ApifyTimeoutError, ApifyActorError


logger = logging.getLogger(__name__)


class ApifyService:
    """
    Service for interacting with Apify actors.

    Handles Amazon review scraping via the axesso_data~amazon-reviews-scraper actor.
    Designed to be extensible for future Apify actors.

    Example:
        service = ApifyService()
        reviews = await service.scrape_reviews(
            asin="B08N5WRWNW",
            domain_code="com",
            max_pages=10,
            filter_by_star=StarFilter.FIVE
        )
    """

    # Actor IDs - use tilde (~) not slash (/)
    ACTOR_IDS = {
        ApifyActorType.REVIEWS: "axesso_data~amazon-reviews-scraper",
        ApifyActorType.PRODUCT_DETAILS: "axesso_data~amazon-product-details-scraper",
    }

    # Marketplace domain mapping
    MARKETPLACE_DOMAINS = {
        "com": "amazon.com",
        "ca": "amazon.ca",
        "co.uk": "amazon.co.uk",
        "de": "amazon.de",
        "fr": "amazon.fr",
        "it": "amazon.it",
        "es": "amazon.es",
        "co.jp": "amazon.co.jp",
        "com.au": "amazon.com.au",
        "com.mx": "amazon.com.mx",
    }

    # Reviews per page (approximation for max_reviews calculation)
    REVIEWS_PER_PAGE = 10

    def __init__(self, api_key: str = None):
        """
        Initialize Apify service.

        Args:
            api_key: Apify API key (defaults to settings value)
        """
        self.api_key = api_key or settings.apify_api_key
        self.client = ApifyClient(self.api_key)

    async def scrape_reviews(
        self,
        asin: str,
        domain_code: str = "com",
        sort_by: str = "recent",
        max_pages: int = 10,
        filter_by_star: str = "all_stars",
        keyword_filter: Optional[str] = None,
        reviewer_type: str = "all_reviews",
    ) -> List[dict]:
        """
        Scrape reviews for a single ASIN.

        Args:
            asin: Amazon ASIN code
            domain_code: Amazon marketplace (com, co.uk, de, etc.)
            sort_by: Sort order (recent, helpful)
            max_pages: Maximum pages to scrape
            filter_by_star: Star rating filter
            keyword_filter: Optional keyword to filter reviews
            reviewer_type: Filter by reviewer type

        Returns:
            List of review dictionaries from Apify

        Raises:
            ApifyError: If API call fails
            ApifyTimeoutError: If actor run times out
        """
        # Build input item for this ASIN
        input_item = {
            "asin": asin,
            "domainCode": domain_code,
            "sortBy": sort_by,
            "maxPages": max_pages,
            "reviewerType": reviewer_type,
        }

        # Only add filterByStar if not "all_stars"
        if filter_by_star and filter_by_star != "all_stars":
            input_item["filterByStar"] = filter_by_star

        if keyword_filter:
            input_item["filterByKeyword"] = keyword_filter

        # Prepare actor input - axesso expects "input" array
        actor_input = {
            "input": [input_item]
        }

        logger.info(f"Starting Apify scrape for ASIN {asin} on amazon.{domain_code}")
        logger.debug(f"Actor input: {actor_input}")

        # Run actor synchronously in thread to avoid blocking
        try:
            reviews = await asyncio.to_thread(
                self._run_actor_sync,
                ApifyActorType.REVIEWS,
                actor_input,
            )
            logger.info(f"Scraped {len(reviews)} reviews for ASIN {asin}")
            return reviews

        except Exception as e:
            logger.error(f"Apify scrape failed for ASIN {asin}: {e}")
            raise ApifyError(f"Failed to scrape reviews: {str(e)}")

    def _run_actor_sync(self, actor_type: ApifyActorType, actor_input: dict) -> List[dict]:
        """
        Run Apify actor synchronously.

        Args:
            actor_type: Type of actor to run
            actor_input: Input configuration for actor

        Returns:
            List of result items from actor run
        """
        actor_id = self.ACTOR_IDS[actor_type]

        # Call actor and wait for results
        run = self.client.actor(actor_id).call(run_input=actor_input)

        if not run:
            raise ApifyActorError("Actor run returned no result")

        # Check run status
        status = run.get("status")
        if status not in ("SUCCEEDED", "RUNNING"):
            error_msg = run.get("statusMessage", "Unknown error")
            raise ApifyActorError(f"Actor run failed: {error_msg}")

        # Fetch results from dataset
        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            raise ApifyActorError("No dataset ID in actor run result")

        items = list(self.client.dataset(dataset_id).iterate_items())
        return items

    # ===== Product Details Scraping =====

    def construct_product_url(self, asin: str, marketplace: str) -> str:
        """
        Construct Amazon product URL from ASIN and marketplace.

        Args:
            asin: Amazon ASIN code
            marketplace: Marketplace code (com, co.uk, de, etc.)

        Returns:
            Full Amazon product URL
        """
        domain = self.MARKETPLACE_DOMAINS.get(marketplace, "amazon.com")
        return f"https://www.{domain}/dp/{asin}"

    async def scrape_product_details(
        self,
        asins: List[str],
        marketplace: str = "com",
    ) -> List[dict]:
        """
        Scrape product details for multiple ASINs.

        The product details scraper can handle batch requests efficiently.

        Args:
            asins: List of Amazon ASIN codes
            marketplace: Amazon marketplace code

        Returns:
            List of product detail dictionaries from Apify

        Raises:
            ApifyError: If API call fails
        """
        # Build URLs for all ASINs
        urls = [self.construct_product_url(asin, marketplace) for asin in asins]

        # Prepare actor input
        actor_input = {"urls": urls}

        logger.info(f"Starting Apify product scrape for {len(asins)} ASINs on {marketplace}")
        logger.debug(f"Actor input: {actor_input}")

        try:
            results = await asyncio.to_thread(
                self._run_actor_sync,
                ApifyActorType.PRODUCT_DETAILS,
                actor_input,
            )
            logger.info(f"Scraped {len(results)} product details")
            return results

        except Exception as e:
            logger.error(f"Apify product scrape failed: {e}")
            raise ApifyError(f"Failed to scrape product details: {str(e)}")

    def scrape_product_details_sync(
        self,
        asins: List[str],
        marketplace: str = "com",
    ) -> List[dict]:
        """
        Synchronous version for use in worker thread.

        Args:
            asins: List of Amazon ASIN codes
            marketplace: Amazon marketplace code

        Returns:
            List of product detail dictionaries from Apify
        """
        urls = [self.construct_product_url(asin, marketplace) for asin in asins]
        actor_input = {"urls": urls}

        logger.info(f"Starting Apify product scrape (sync) for {len(asins)} ASINs")

        try:
            results = self._run_actor_sync(
                ApifyActorType.PRODUCT_DETAILS,
                actor_input,
            )
            logger.info(f"Scraped {len(results)} product details")
            return results

        except Exception as e:
            logger.error(f"Apify product scrape failed: {e}")
            raise ApifyError(f"Failed to scrape product details: {str(e)}")

    @staticmethod
    def parse_rating(rating_str: str) -> Optional[float]:
        """
        Parse rating string from Apify response.

        Converts "4.5 out of 5 stars" to 4.5

        Args:
            rating_str: Rating string from Apify

        Returns:
            Float rating value or None if parsing fails
        """
        import re

        if not rating_str:
            return None

        match = re.search(r"(\d+\.?\d*)\s*out of", rating_str)
        if match:
            return float(match.group(1))

        # Try direct float conversion as fallback
        try:
            return float(rating_str)
        except (ValueError, TypeError):
            return None

    async def check_api_key(self) -> bool:
        """
        Verify Apify API key is valid.

        Returns:
            True if API key is valid, False otherwise
        """
        try:
            user = await asyncio.to_thread(
                lambda: self.client.user().get()
            )
            return user is not None
        except Exception:
            return False

    @staticmethod
    def parse_competitor_data(raw_data: dict, pack_size: int = 1) -> dict:
        """
        Parse Apify product details response into competitor_data fields.

        Maps the axesso_data~amazon-product-details-scraper output to our
        CompetitorData model fields.

        Args:
            raw_data: Raw response from Apify product details scraper
            pack_size: Pack size for unit price calculation

        Returns:
            Dictionary with parsed competitor data fields
        """
        import re
        from decimal import Decimal, InvalidOperation

        def parse_price(price_val) -> Optional[Decimal]:
            """Extract numeric price from various formats."""
            if price_val is None:
                return None
            if isinstance(price_val, (int, float)):
                return Decimal(str(price_val))
            if isinstance(price_val, str):
                # Remove currency symbols and extract number
                match = re.search(r"[\d,]+\.?\d*", price_val.replace(",", ""))
                if match:
                    try:
                        return Decimal(match.group())
                    except InvalidOperation:
                        return None
            return None

        def parse_rating_value(rating_val) -> Optional[float]:
            """Extract rating from various formats."""
            if rating_val is None:
                return None
            if isinstance(rating_val, (int, float)):
                return float(rating_val)
            if isinstance(rating_val, str):
                # Handle "4.5 out of 5 stars" format
                match = re.search(r"(\d+\.?\d*)", rating_val)
                if match:
                    return float(match.group(1))
            return None

        def parse_int(val) -> Optional[int]:
            """Extract integer from various formats."""
            if val is None:
                return None
            if isinstance(val, int):
                return val
            if isinstance(val, str):
                # Remove commas and extract number
                match = re.search(r"[\d,]+", val.replace(",", ""))
                if match:
                    try:
                        return int(match.group().replace(",", ""))
                    except ValueError:
                        return None
            return None

        # Extract main fields
        price = parse_price(raw_data.get("price"))
        rating = parse_rating_value(
            raw_data.get("productRating") or raw_data.get("rating")
        )
        review_count = parse_int(
            raw_data.get("countReview")
            or raw_data.get("reviewsCount")
            or raw_data.get("reviews")
        )

        # Calculate unit price
        unit_price = None
        if price is not None and pack_size and pack_size > 0:
            unit_price = price / Decimal(str(pack_size))

        return {
            "title": raw_data.get("title"),
            "brand": raw_data.get("brand"),
            "manufacturer": raw_data.get("manufacturer"),
            "price": price,
            "retail_price": parse_price(raw_data.get("retailPrice") or raw_data.get("listPrice")),
            "shipping_price": parse_price(raw_data.get("shippingPrice")),
            "currency": raw_data.get("currency"),
            "unit_price": unit_price,
            "price_saving": raw_data.get("priceSaving") or raw_data.get("savings"),
            "rating": rating,
            "review_count": review_count,
            "past_sales": raw_data.get("pastSales") or raw_data.get("soldLastMonth"),
            "availability": (
                raw_data.get("warehouseAvailability")
                or raw_data.get("availability")
                or raw_data.get("inStock")
            ),
            "sold_by": raw_data.get("soldBy") or raw_data.get("sellerName"),
            "fulfilled_by": raw_data.get("fulfilledBy"),
            "seller_id": raw_data.get("sellerId"),
            "is_prime": raw_data.get("prime", False) or raw_data.get("isPrime", False),
            "features": raw_data.get("features") or raw_data.get("bulletPoints"),
            "product_description": raw_data.get("description") or raw_data.get("productDescription"),
            "main_image_url": (
                raw_data.get("mainImage", {}).get("imageUrl")
                if isinstance(raw_data.get("mainImage"), dict)
                else raw_data.get("mainImage") or raw_data.get("imageUrl")
            ),
            "images": (
                raw_data.get("imageUrlList")
                or raw_data.get("images")
                or raw_data.get("imageUrls")
            ),
            "videos": raw_data.get("videoeUrlList") or raw_data.get("videos"),
            "categories": (
                raw_data.get("categoriesExtended")
                or raw_data.get("categories")
                or raw_data.get("breadcrumbs")
            ),
            "variations": raw_data.get("variations"),
            "variations_count": len(raw_data.get("variations", [])) if raw_data.get("variations") else 0,
            "product_details": raw_data.get("productDetails") or raw_data.get("specifications"),
            "review_insights": raw_data.get("reviewInsights"),
            "raw_data": raw_data,
        }


# Singleton instance for easy access
_apify_service: Optional[ApifyService] = None


def get_apify_service() -> ApifyService:
    """
    Get or create Apify service singleton.

    Returns:
        ApifyService instance
    """
    global _apify_service
    if _apify_service is None:
        _apify_service = ApifyService()
    return _apify_service
