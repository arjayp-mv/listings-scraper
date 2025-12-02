# =============================================================================
# Reviews Domain - Business Logic
# =============================================================================
# Purpose: Service layer for review operations
# Public API: ReviewService
# Dependencies: sqlalchemy, models, schemas
# =============================================================================

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import Review
from ..jobs.models import ScrapeJob, JobAsin


class ReviewService:
    """
    Service class for review business logic.

    Handles review storage, queries, and formatting.
    """

    def __init__(self, db: Session):
        self.db = db

    # ===== Review Storage =====

    def save_reviews(
        self,
        job_asin: JobAsin,
        reviews: List[dict],
    ) -> int:
        """
        Save reviews from Apify response.

        Deduplicates by review_id to avoid duplicates.

        Args:
            job_asin: JobAsin record these reviews belong to
            reviews: List of review dicts from Apify

        Returns:
            Count of reviews saved (excluding duplicates)
        """
        saved_count = 0

        for review_data in reviews:
            review_id = review_data.get("reviewId")

            # Skip if review already exists
            if review_id:
                existing = (
                    self.db.query(Review)
                    .filter(Review.review_id == review_id)
                    .first()
                )
                if existing:
                    continue

            # Create review record
            # Apify axesso actor uses: title, text, rating, date, userName, verified
            review = Review(
                job_asin_id=job_asin.id,
                review_id=review_id,
                title=review_data.get("title"),
                text=review_data.get("text"),
                rating=review_data.get("rating"),
                date=review_data.get("date"),
                user_name=review_data.get("userName"),
                verified=review_data.get("verified", False),
                helpful_count=review_data.get("numberOfHelpful", 0),
                raw_data=review_data,
            )
            self.db.add(review)
            saved_count += 1

        self.db.commit()
        return saved_count

    # ===== Review Queries =====

    def get_reviews_for_job(
        self,
        job_id: int,
        offset: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        rating: Optional[str] = None,
        asin: Optional[str] = None,
    ) -> tuple[List[Review], int]:
        """
        Get reviews for a job with filters.

        Args:
            job_id: Job ID to get reviews for
            offset: Pagination offset
            limit: Page size
            search: Optional search term for title/text
            rating: Optional rating filter
            asin: Optional ASIN filter

        Returns:
            Tuple of (review list, total count)
        """
        # Join with job_asin to filter by job
        query = (
            self.db.query(Review)
            .join(JobAsin)
            .filter(JobAsin.job_id == job_id)
        )

        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Review.title.ilike(search_term)) |
                (Review.text.ilike(search_term))
            )

        if rating:
            query = query.filter(Review.rating == rating)

        if asin:
            query = query.filter(JobAsin.asin == asin.upper())

        # Order by most recent first
        query = query.order_by(Review.id.desc())

        total = query.count()
        items = query.offset(offset).limit(limit).all()
        return items, total

    def get_all_reviews_for_job(
        self,
        job_id: int,
        search: Optional[str] = None,
        rating: Optional[str] = None,
    ) -> List[Review]:
        """
        Get all reviews for a job (no pagination).

        Used for export and formatting.
        """
        query = (
            self.db.query(Review)
            .join(JobAsin)
            .filter(JobAsin.job_id == job_id)
        )

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Review.title.ilike(search_term)) |
                (Review.text.ilike(search_term))
            )

        if rating:
            query = query.filter(Review.rating == rating)

        return query.order_by(Review.id).all()

    # ===== Formatted Output =====

    def get_formatted_reviews(
        self,
        job_id: int,
        search: Optional[str] = None,
        rating: Optional[str] = None,
    ) -> dict:
        """
        Get reviews formatted for copy/paste.

        Returns:
            Dict with reviews list, total count, and formatted text
        """
        reviews = self.get_all_reviews_for_job(job_id, search, rating)

        formatted_items = []
        text_parts = []

        for review in reviews:
            title = review.title or ""
            text = review.text or ""

            # Skip empty reviews
            if not title and not text:
                continue

            formatted_items.append({
                "title": title,
                "text": text,
            })

            # Build formatted text block
            text_parts.append(f"{title}\n{text}")

        # Join with double newline between reviews
        formatted_text = "\n\n".join(text_parts)

        return {
            "reviews": formatted_items,
            "total": len(formatted_items),
            "formatted_text": formatted_text,
        }

    # ===== Statistics =====

    def get_review_stats(self, job_id: int) -> dict:
        """
        Get review statistics for a job.

        Uses database aggregation per best practices.
        """
        # Get reviews for job
        query = (
            self.db.query(Review)
            .join(JobAsin)
            .filter(JobAsin.job_id == job_id)
        )

        total = query.count()
        verified = query.filter(Review.verified == True).count()

        # Count by rating
        five_star = query.filter(Review.rating.like("%5%")).count()
        four_star = query.filter(Review.rating.like("%4%")).count()
        three_star = query.filter(Review.rating.like("%3%")).count()
        two_star = query.filter(Review.rating.like("%2%")).count()
        one_star = query.filter(Review.rating.like("%1%")).count()

        # Calculate average
        total_rated = five_star + four_star + three_star + two_star + one_star
        average = None
        if total_rated > 0:
            weighted_sum = (5 * five_star + 4 * four_star + 3 * three_star +
                           2 * two_star + 1 * one_star)
            average = round(weighted_sum / total_rated, 2)

        return {
            "total_reviews": total,
            "five_star": five_star,
            "four_star": four_star,
            "three_star": three_star,
            "two_star": two_star,
            "one_star": one_star,
            "verified_count": verified,
            "average_rating": average,
        }
