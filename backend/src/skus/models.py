# =============================================================================
# SKU Domain - SQLAlchemy Models
# =============================================================================
# Purpose: Database models for SKU management
# Public API: Sku
# Dependencies: sqlalchemy, database
# =============================================================================

from sqlalchemy import Column, BigInteger, String, Text, TIMESTAMP, func
from sqlalchemy.orm import relationship

from ..database import Base


class Sku(Base):
    """
    SKU model for organizing scrape jobs by product.

    Attributes:
        id: Primary key
        sku_code: Unique identifier (e.g., "WF2", "WF3")
        description: Optional description of the SKU
        created_at: Timestamp when SKU was created
        updated_at: Timestamp of last update
        jobs: Relationship to associated scrape jobs
    """

    __tablename__ = "sku"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sku_code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    jobs = relationship("ScrapeJob", back_populates="sku")
