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
