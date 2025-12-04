# =============================================================================
# Channel SKUs Domain - SQLAlchemy Models
# =============================================================================
# Purpose: Database models for Channel SKU management and ASIN history
# Public API: ChannelSku, ChannelSkuAsinHistory
# Dependencies: sqlalchemy, database
# =============================================================================

from sqlalchemy import (
    Column,
    BigInteger,
    String,
    DECIMAL,
    Integer,
    TIMESTAMP,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.orm import relationship

from ..database import Base


class ChannelSku(Base):
    """
    Channel SKU model for tracking own Amazon listings.

    Attributes:
        id: Primary key
        sku_id: Optional FK to parent SKU for grouping
        channel_sku_code: Channel SKU identifier (e.g., "ABC-123")
        marketplace: Amazon marketplace (com, ca, co.uk, etc.)
        current_asin: Current ASIN mapped to this Channel SKU
        pack_size: Number of units in pack (for unit price calculation)
        product_title: Cached product title from last scan
        latest_rating: Latest scraped rating (e.g., 4.5)
        latest_review_count: Latest scraped review count
        last_scraped_at: Timestamp of last successful scan
        created_at: Timestamp when record was created
        updated_at: Timestamp of last update
    """

    __tablename__ = "channel_sku"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sku_id = Column(BigInteger, ForeignKey("sku.id", ondelete="SET NULL"), nullable=True)
    channel_sku_code = Column(String(100), nullable=False)
    marketplace = Column(String(10), nullable=False, default="com")
    current_asin = Column(String(15), nullable=False)
    pack_size = Column(Integer, nullable=True, default=1)
    product_title = Column(String(500), nullable=True)
    latest_rating = Column(DECIMAL(2, 1), nullable=True)
    latest_review_count = Column(Integer, nullable=True)
    last_scraped_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    sku = relationship("Sku", backref="channel_skus")
    asin_history = relationship(
        "ChannelSkuAsinHistory",
        back_populates="channel_sku",
        cascade="all, delete-orphan",
    )
    scan_items = relationship(
        "ProductScanItem",
        back_populates="channel_sku",
        cascade="all, delete-orphan",
    )

    # Composite unique constraint
    __table_args__ = (
        Index("idx_channel_sku_sku_id", "sku_id"),
        Index("idx_channel_sku_rating", "latest_rating"),
        Index("idx_channel_sku_marketplace", "marketplace"),
    )


class ChannelSkuAsinHistory(Base):
    """
    Track ASIN changes for Channel SKUs over time.

    Attributes:
        id: Primary key
        channel_sku_id: FK to channel_sku
        asin: The ASIN that was assigned
        changed_at: When the ASIN was changed
        changed_by_job_id: Product scan job that detected the change
    """

    __tablename__ = "channel_sku_asin_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    channel_sku_id = Column(
        BigInteger,
        ForeignKey("channel_sku.id", ondelete="CASCADE"),
        nullable=False,
    )
    asin = Column(String(15), nullable=False)
    changed_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    changed_by_job_id = Column(BigInteger, nullable=True)

    # Relationships
    channel_sku = relationship("ChannelSku", back_populates="asin_history")

    __table_args__ = (Index("idx_asin_history_channel_sku", "channel_sku_id"),)
