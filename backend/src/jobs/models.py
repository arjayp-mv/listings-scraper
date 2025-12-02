# =============================================================================
# Jobs Domain - SQLAlchemy Models
# =============================================================================
# Purpose: Database models for scrape job and ASIN tracking
# Public API: ScrapeJob, JobAsin
# Dependencies: sqlalchemy, database
# =============================================================================

from sqlalchemy import (
    Column, BigInteger, String, Text, Integer, Enum, JSON, TIMESTAMP,
    ForeignKey, func
)
from sqlalchemy.orm import relationship

from ..database import Base


class ScrapeJob(Base):
    """
    Scrape job model tracking a scraping task and its configuration.

    Attributes:
        id: Primary key
        sku_id: Foreign key to associated SKU (optional)
        job_name: User-provided name for the job
        status: Current job status
        marketplace: Amazon domain (com, co.uk, de, etc.)
        sort_by: Review sort order
        max_pages: Maximum pages to scrape per ASIN
        star_filters: JSON array of star filters to apply
        keyword_filter: Optional keyword to filter reviews
        reviewer_type: Filter by reviewer type
        total_asins: Count of ASINs in job
        completed_asins: Count of successfully scraped ASINs
        failed_asins: Count of failed ASINs
        total_reviews: Total reviews collected
        apify_delay_seconds: Delay between Apify calls
        error_message: Error details if job failed
        created_at: Job creation timestamp
        started_at: When job started processing
        completed_at: When job finished
    """

    __tablename__ = "scrape_job"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sku_id = Column(BigInteger, ForeignKey("sku.id", ondelete="SET NULL"), nullable=True)
    job_name = Column(String(255), nullable=False)
    status = Column(
        Enum("queued", "running", "completed", "partial", "failed", "cancelled"),
        default="queued",
    )
    marketplace = Column(String(10), default="com")
    sort_by = Column(String(20), default="recent")
    max_pages = Column(Integer, default=10)
    star_filters = Column(JSON, nullable=True)
    keyword_filter = Column(String(255), nullable=True)
    reviewer_type = Column(String(20), default="all_reviews")
    total_asins = Column(Integer, default=0)
    completed_asins = Column(Integer, default=0)
    failed_asins = Column(Integer, default=0)
    total_reviews = Column(Integer, default=0)
    apify_delay_seconds = Column(Integer, default=10)
    error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    sku = relationship("Sku", back_populates="jobs")
    asins = relationship("JobAsin", back_populates="job", cascade="all, delete-orphan")


class JobAsin(Base):
    """
    Individual ASIN within a scrape job.

    Tracks the status and results for each ASIN being scraped.

    Attributes:
        id: Primary key
        job_id: Parent job reference
        asin: Amazon ASIN code
        product_title: Fetched product title
        status: Processing status
        reviews_found: Number of reviews collected
        apify_run_id: Apify actor run ID
        error_message: Error details if failed
        started_at: When ASIN processing began
        completed_at: When ASIN processing finished
    """

    __tablename__ = "job_asin"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(
        BigInteger,
        ForeignKey("scrape_job.id", ondelete="CASCADE"),
        nullable=False,
    )
    asin = Column(String(15), nullable=False)
    product_title = Column(String(500), nullable=True)
    status = Column(
        Enum("pending", "running", "completed", "failed"),
        default="pending",
    )
    reviews_found = Column(Integer, default=0)
    apify_run_id = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    job = relationship("ScrapeJob", back_populates="asins")
    reviews = relationship("Review", back_populates="job_asin", cascade="all, delete-orphan")
