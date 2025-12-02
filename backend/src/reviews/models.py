# =============================================================================
# Reviews Domain - SQLAlchemy Models
# =============================================================================
# Purpose: Database models for review storage
# Public API: Review, AsinHistory
# Dependencies: sqlalchemy, database
# =============================================================================

from sqlalchemy import (
    Column, BigInteger, String, Text, Integer, Boolean, JSON, TIMESTAMP,
    ForeignKey, func, Index
)
from sqlalchemy.orm import relationship

from ..database import Base


class Review(Base):
    """
    Amazon review model storing scraped review data.

    Attributes:
        id: Primary key
        job_asin_id: Reference to parent JobAsin
        review_id: Amazon's unique review ID (for deduplication)
        title: Review title/headline
        text: Full review text
        rating: Star rating as string
        date: Review date as displayed on Amazon
        user_name: Reviewer's display name
        verified: Whether purchase was verified
        helpful_count: Number of helpful votes
        raw_data: Full JSON response from Apify
        created_at: When review was stored
    """

    __tablename__ = "review"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_asin_id = Column(
        BigInteger,
        ForeignKey("job_asin.id", ondelete="CASCADE"),
        nullable=False,
    )
    review_id = Column(String(50), unique=True, nullable=True)
    title = Column(String(500), nullable=True)
    text = Column(Text, nullable=True)
    rating = Column(String(20), nullable=True)
    date = Column(String(100), nullable=True)
    user_name = Column(String(200), nullable=True)
    verified = Column(Boolean, default=False)
    helpful_count = Column(Integer, default=0)
    raw_data = Column(JSON, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    # Relationships
    job_asin = relationship("JobAsin", back_populates="reviews")

    # Note: FULLTEXT index is created in the SQL schema file
    # SQLAlchemy doesn't directly support FULLTEXT indexes


class AsinHistory(Base):
    """
    Track ASIN scraping history across jobs.

    Used to warn users when an ASIN has been scraped before,
    helping avoid duplicate work.

    Attributes:
        id: Primary key
        asin: Amazon ASIN code
        marketplace: Amazon marketplace domain
        last_scraped_job_id: Most recent job that scraped this ASIN
        last_scraped_at: When ASIN was last scraped
        total_scrapes: Number of times this ASIN has been scraped
    """

    __tablename__ = "asin_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    asin = Column(String(15), nullable=False)
    marketplace = Column(String(10), nullable=False)
    last_scraped_job_id = Column(
        BigInteger,
        ForeignKey("scrape_job.id", ondelete="SET NULL"),
        nullable=True,
    )
    last_scraped_at = Column(TIMESTAMP, nullable=True)
    total_scrapes = Column(Integer, default=1)

    # Composite unique constraint handled in SQL schema
    __table_args__ = (
        Index("idx_asin_history_asin", "asin"),
    )
