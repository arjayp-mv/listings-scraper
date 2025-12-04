# =============================================================================
# Competitors Domain - SQLAlchemy Models
# =============================================================================
# Purpose: Database models for competitor tracking and research
# Public API: Competitor, CompetitorData, CompetitorPriceHistory,
#             CompetitorKeyword, KeywordChannelSkuLink, KeywordCompetitorLink,
#             CompetitorScrapeJob, CompetitorScrapeItem
# Dependencies: sqlalchemy, database
# =============================================================================

from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Text,
    Boolean,
    Integer,
    DECIMAL,
    TIMESTAMP,
    ForeignKey,
    Enum,
    Index,
    func,
)
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import relationship

from ..database import Base


class Competitor(Base):
    """
    Competitor model for tracking individual competitor ASINs.

    Attributes:
        id: Primary key
        sku_id: Optional FK to parent SKU for grouping
        asin: Amazon ASIN being tracked
        marketplace: Amazon marketplace (com, ca, co.uk, etc.)
        pack_size: Number of units in pack (for unit price calculation)
        display_name: Human-readable name for this competitor
        schedule: Scraping schedule frequency
        next_scrape_at: Next scheduled scrape time
        is_active: Whether competitor is actively being tracked
        notes: Optional notes about this competitor
    """

    __tablename__ = "competitor"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sku_id = Column(
        BigInteger, ForeignKey("sku.id", ondelete="SET NULL"), nullable=True
    )
    asin = Column(String(15), nullable=False)
    marketplace = Column(String(10), nullable=False, default="com")
    pack_size = Column(Integer, nullable=True, default=1)
    display_name = Column(String(255), nullable=True)
    schedule = Column(
        Enum(
            "none",
            "daily",
            "every_2_days",
            "every_3_days",
            "weekly",
            "monthly",
            name="schedule_enum",
        ),
        default="none",
    )
    next_scrape_at = Column(TIMESTAMP, nullable=True)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    sku = relationship("Sku", backref="competitors")
    data = relationship(
        "CompetitorData",
        back_populates="competitor",
        uselist=False,
        cascade="all, delete-orphan",
    )
    price_history = relationship(
        "CompetitorPriceHistory",
        back_populates="competitor",
        cascade="all, delete-orphan",
    )
    keyword_links = relationship(
        "KeywordCompetitorLink",
        back_populates="competitor",
        cascade="all, delete-orphan",
    )
    scrape_items = relationship(
        "CompetitorScrapeItem",
        back_populates="competitor",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_competitor_sku_id", "sku_id"),
        Index("idx_competitor_schedule", "schedule", "next_scrape_at"),
        Index("idx_competitor_active", "is_active"),
        Index("idx_competitor_marketplace", "marketplace"),
        Index(
            "unique_competitor_asin_marketplace", "asin", "marketplace", unique=True
        ),
    )


class CompetitorData(Base):
    """
    Latest scraped data for a competitor (1:1 with competitor).

    Attributes:
        id: Primary key
        competitor_id: FK to competitor
        title: Product title
        brand: Product brand
        manufacturer: Product manufacturer
        price: Current price
        retail_price: MSRP/list price
        shipping_price: Shipping cost
        currency: Currency code
        unit_price: Calculated price per unit
        price_saving: Savings description
        rating: Product rating (1-5)
        review_count: Number of reviews
        past_sales: Past sales indicator
        availability: Stock status
        sold_by: Seller name
        fulfilled_by: Fulfillment provider
        seller_id: Amazon seller ID
        is_prime: Prime eligible
        features: Bullet points (JSON array)
        product_description: Full product description
        main_image_url: Primary product image
        images: All images (JSON array)
        videos: Product videos (JSON array)
        categories: Category breadcrumb (JSON array)
        variations: Product variations (JSON object)
        variations_count: Number of variations
        product_details: Additional details table (JSON object)
        review_insights: Review analysis data (JSON object)
        raw_data: Complete raw Apify response
        scraped_at: When data was last scraped
    """

    __tablename__ = "competitor_data"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    competitor_id = Column(
        BigInteger,
        ForeignKey("competitor.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    title = Column(String(500), nullable=True)
    brand = Column(String(255), nullable=True)
    manufacturer = Column(String(255), nullable=True)
    price = Column(DECIMAL(10, 2), nullable=True)
    retail_price = Column(DECIMAL(10, 2), nullable=True)
    shipping_price = Column(DECIMAL(10, 2), nullable=True)
    currency = Column(String(10), nullable=True)
    unit_price = Column(DECIMAL(10, 4), nullable=True)
    price_saving = Column(String(100), nullable=True)
    rating = Column(DECIMAL(2, 1), nullable=True)
    review_count = Column(Integer, nullable=True)
    past_sales = Column(String(100), nullable=True)
    availability = Column(String(100), nullable=True)
    sold_by = Column(String(255), nullable=True)
    fulfilled_by = Column(String(255), nullable=True)
    seller_id = Column(String(50), nullable=True)
    is_prime = Column(Boolean, default=False)
    features = Column(LONGTEXT, nullable=True)  # JSON stored as text for PyMySQL
    product_description = Column(Text, nullable=True)
    main_image_url = Column(String(500), nullable=True)
    images = Column(LONGTEXT, nullable=True)  # JSON stored as text for PyMySQL
    videos = Column(LONGTEXT, nullable=True)  # JSON stored as text for PyMySQL
    categories = Column(LONGTEXT, nullable=True)  # JSON stored as text for PyMySQL
    variations = Column(LONGTEXT, nullable=True)  # JSON stored as text for PyMySQL
    variations_count = Column(Integer, default=0)
    product_details = Column(LONGTEXT, nullable=True)  # JSON stored as text for PyMySQL
    review_insights = Column(LONGTEXT, nullable=True)  # JSON stored as text for PyMySQL
    raw_data = Column(LONGTEXT, nullable=True)  # JSON stored as text for PyMySQL
    scraped_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    competitor = relationship("Competitor", back_populates="data")

    __table_args__ = (Index("idx_competitor_data_scraped", "scraped_at"),)


class CompetitorPriceHistory(Base):
    """
    Historical price/rating data for competitors (1 year retention).

    Attributes:
        id: Primary key
        competitor_id: FK to competitor
        price: Price at time of scrape
        unit_price: Unit price at time of scrape
        shipping_price: Shipping cost at time of scrape
        availability: Stock status at time of scrape
        rating: Rating at time of scrape
        review_count: Review count at time of scrape
        scraped_at: When this data was captured
    """

    __tablename__ = "competitor_price_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    competitor_id = Column(
        BigInteger,
        ForeignKey("competitor.id", ondelete="CASCADE"),
        nullable=False,
    )
    price = Column(DECIMAL(10, 2), nullable=True)
    unit_price = Column(DECIMAL(10, 4), nullable=True)
    shipping_price = Column(DECIMAL(10, 2), nullable=True)
    availability = Column(String(100), nullable=True)
    rating = Column(DECIMAL(2, 1), nullable=True)
    review_count = Column(Integer, nullable=True)
    scraped_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    # Relationships
    competitor = relationship("Competitor", back_populates="price_history")

    __table_args__ = (
        Index("idx_price_history_competitor", "competitor_id"),
        Index("idx_price_history_scraped", "scraped_at"),
        Index("idx_price_history_comp_date", "competitor_id", "scraped_at"),
    )


class CompetitorKeyword(Base):
    """
    Keywords for competitor research.

    Attributes:
        id: Primary key
        sku_id: Optional FK to parent SKU for grouping
        keyword: The keyword/search term
        marketplace: Amazon marketplace
        notes: Optional notes about this keyword
    """

    __tablename__ = "competitor_keyword"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sku_id = Column(
        BigInteger, ForeignKey("sku.id", ondelete="SET NULL"), nullable=True
    )
    keyword = Column(String(255), nullable=False)
    marketplace = Column(String(10), nullable=False, default="com")
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    sku = relationship("Sku", backref="competitor_keywords")
    channel_sku_links = relationship(
        "KeywordChannelSkuLink",
        back_populates="keyword",
        cascade="all, delete-orphan",
    )
    competitor_links = relationship(
        "KeywordCompetitorLink",
        back_populates="keyword",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_keyword_sku_id", "sku_id"),
        Index("idx_keyword_marketplace", "marketplace"),
        Index("idx_keyword_text", "keyword"),
    )


class KeywordChannelSkuLink(Base):
    """
    Many-to-many link between keywords and channel SKUs.

    Attributes:
        id: Primary key
        keyword_id: FK to competitor_keyword
        channel_sku_id: FK to channel_sku
    """

    __tablename__ = "keyword_channel_sku_link"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    keyword_id = Column(
        BigInteger,
        ForeignKey("competitor_keyword.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel_sku_id = Column(
        BigInteger,
        ForeignKey("channel_sku.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    # Relationships
    keyword = relationship("CompetitorKeyword", back_populates="channel_sku_links")
    channel_sku = relationship("ChannelSku", backref="keyword_links")

    __table_args__ = (
        Index("idx_link_keyword", "keyword_id"),
        Index("idx_link_channel_sku", "channel_sku_id"),
        Index(
            "unique_keyword_channel_sku",
            "keyword_id",
            "channel_sku_id",
            unique=True,
        ),
    )


class KeywordCompetitorLink(Base):
    """
    Many-to-many link between keywords and competitors.

    Attributes:
        id: Primary key
        keyword_id: FK to competitor_keyword
        competitor_id: FK to competitor
    """

    __tablename__ = "keyword_competitor_link"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    keyword_id = Column(
        BigInteger,
        ForeignKey("competitor_keyword.id", ondelete="CASCADE"),
        nullable=False,
    )
    competitor_id = Column(
        BigInteger,
        ForeignKey("competitor.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    # Relationships
    keyword = relationship("CompetitorKeyword", back_populates="competitor_links")
    competitor = relationship("Competitor", back_populates="keyword_links")

    __table_args__ = (
        Index("idx_link_keyword_comp", "keyword_id"),
        Index("idx_link_competitor", "competitor_id"),
        Index(
            "unique_keyword_competitor",
            "keyword_id",
            "competitor_id",
            unique=True,
        ),
    )


class CompetitorScrapeJob(Base):
    """
    Batch scrape job for competitors.

    Attributes:
        id: Primary key
        job_name: Human-readable job name
        status: Current job status
        job_type: Manual or scheduled
        marketplace: Target marketplace
        total_competitors: Total competitors to scrape
        completed_competitors: Successfully scraped count
        failed_competitors: Failed scrape count
        error_message: Error details if failed
        created_at: When job was created
        started_at: When job started processing
        completed_at: When job finished
    """

    __tablename__ = "competitor_scrape_job"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_name = Column(String(255), nullable=False)
    status = Column(
        Enum(
            "queued",
            "running",
            "completed",
            "partial",
            "failed",
            "cancelled",
            name="comp_job_status_enum",
        ),
        default="queued",
    )
    job_type = Column(
        Enum("manual", "scheduled", name="comp_job_type_enum"),
        default="manual",
    )
    marketplace = Column(String(10), nullable=False, default="com")
    total_competitors = Column(Integer, default=0)
    completed_competitors = Column(Integer, default=0)
    failed_competitors = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    items = relationship(
        "CompetitorScrapeItem",
        back_populates="job",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_comp_job_status", "status"),
        Index("idx_comp_job_created", "created_at"),
    )


class CompetitorScrapeItem(Base):
    """
    Individual item within a competitor scrape job.

    Attributes:
        id: Primary key
        job_id: FK to competitor_scrape_job
        competitor_id: FK to competitor being scraped
        input_asin: ASIN being scraped
        status: Item status
        error_message: Error details if failed
        apify_run_id: Apify run ID for tracking
        started_at: When item started processing
        completed_at: When item finished
    """

    __tablename__ = "competitor_scrape_item"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(
        BigInteger,
        ForeignKey("competitor_scrape_job.id", ondelete="CASCADE"),
        nullable=False,
    )
    competitor_id = Column(
        BigInteger,
        ForeignKey("competitor.id", ondelete="CASCADE"),
        nullable=False,
    )
    input_asin = Column(String(15), nullable=False)
    status = Column(
        Enum(
            "pending",
            "running",
            "completed",
            "failed",
            name="comp_item_status_enum",
        ),
        default="pending",
    )
    error_message = Column(Text, nullable=True)
    apify_run_id = Column(String(50), nullable=True)
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)

    # Relationships
    job = relationship("CompetitorScrapeJob", back_populates="items")
    competitor = relationship("Competitor", back_populates="scrape_items")

    __table_args__ = (
        Index("idx_comp_item_job_status", "job_id", "status"),
        Index("idx_comp_item_competitor", "competitor_id"),
    )
