# =============================================================================
# Product Scans Domain - SQLAlchemy Models
# =============================================================================
# Purpose: Database models for product scan jobs and items
# Public API: ProductScanJob, ProductScanItem
# Dependencies: sqlalchemy, database
# =============================================================================

from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    DECIMAL,
    Integer,
    Enum,
    TIMESTAMP,
    ForeignKey,
    Index,
    JSON,
    func,
)
from sqlalchemy.orm import relationship
import enum

from ..database import Base


class JobStatus(str, enum.Enum):
    """Status enum for product scan jobs."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ItemStatus(str, enum.Enum):
    """Status enum for individual scan items."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ProductScanJob(Base):
    """
    Product scan job for scraping metrics from Amazon listings.

    Attributes:
        id: Primary key
        job_name: User-provided job name
        status: Job status (queued, running, completed, etc.)
        marketplace: Amazon marketplace for all items
        total_listings: Total number of listings to scan
        completed_listings: Number successfully completed
        failed_listings: Number that failed
        error_message: Error message if job failed
        created_at: When job was created
        started_at: When processing started
        completed_at: When processing finished
    """

    __tablename__ = "product_scan_job"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_name = Column(String(255), nullable=False)
    status = Column(
        Enum(JobStatus, values_callable=lambda x: [e.value for e in x]),
        default=JobStatus.QUEUED,
        nullable=False,
    )
    marketplace = Column(String(10), nullable=False, default="com")
    total_listings = Column(Integer, default=0)
    completed_listings = Column(Integer, default=0)
    failed_listings = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    items = relationship(
        "ProductScanItem",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_product_scan_status", "status"),
        Index("idx_product_scan_created", "created_at", postgresql_ops={"created_at": "DESC"}),
    )


class ProductScanItem(Base):
    """
    Individual listing within a product scan job.

    Attributes:
        id: Primary key
        job_id: FK to product_scan_job
        channel_sku_id: FK to channel_sku
        input_asin: ASIN to scrape
        status: Item status (pending, running, completed, failed)
        scraped_rating: Rating returned from scrape
        scraped_review_count: Review count returned
        scraped_title: Product title returned
        scraped_asin: ASIN returned (for change detection)
        apify_run_id: Apify run ID for debugging
        error_message: Error if item failed
        raw_data: Full Apify response JSON
        started_at: When scraping started
        completed_at: When scraping finished
    """

    __tablename__ = "product_scan_item"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(
        BigInteger,
        ForeignKey("product_scan_job.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel_sku_id = Column(
        BigInteger,
        ForeignKey("channel_sku.id", ondelete="CASCADE"),
        nullable=False,
    )
    input_asin = Column(String(15), nullable=False)
    status = Column(
        Enum(ItemStatus, values_callable=lambda x: [e.value for e in x]),
        default=ItemStatus.PENDING,
        nullable=False,
    )
    scraped_rating = Column(DECIMAL(2, 1), nullable=True)
    scraped_review_count = Column(Integer, nullable=True)
    scraped_title = Column(String(500), nullable=True)
    scraped_asin = Column(String(15), nullable=True)
    apify_run_id = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    raw_data = Column(JSON, nullable=True)
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    job = relationship("ProductScanJob", back_populates="items")
    channel_sku = relationship("ChannelSku", back_populates="scan_items")

    __table_args__ = (
        Index("idx_scan_item_job_status", "job_id", "status"),
        Index("idx_scan_item_channel_sku", "channel_sku_id"),
    )
