# =============================================================================
# SKU Domain - Business Logic
# =============================================================================
# Purpose: Service layer for SKU operations
# Public API: SkuService
# Dependencies: sqlalchemy, models, schemas
# =============================================================================

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from .models import Sku
from ..jobs.models import ScrapeJob


class SkuService:
    """
    Service class for SKU business logic.

    Handles CRUD operations and queries for SKUs.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, sku_code: str, description: Optional[str] = None) -> Sku:
        """
        Create a new SKU.

        Args:
            sku_code: Unique SKU identifier
            description: Optional description

        Returns:
            Created SKU instance
        """
        sku = Sku(sku_code=sku_code, description=description)
        self.db.add(sku)
        self.db.commit()
        self.db.refresh(sku)
        return sku

    def get_by_id(self, sku_id: int) -> Optional[Sku]:
        """Get SKU by ID."""
        return self.db.query(Sku).filter(Sku.id == sku_id).first()

    def get_by_code(self, sku_code: str) -> Optional[Sku]:
        """Get SKU by code."""
        return self.db.query(Sku).filter(Sku.sku_code == sku_code).first()

    def get_or_create(self, sku_code: str, description: Optional[str] = None) -> Sku:
        """
        Get existing SKU or create new one.

        Args:
            sku_code: SKU code to find or create
            description: Description for new SKU

        Returns:
            Existing or newly created SKU
        """
        sku = self.get_by_code(sku_code)
        if sku:
            return sku
        return self.create(sku_code, description)

    def update(
        self,
        sku: Sku,
        sku_code: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Sku:
        """
        Update SKU fields.

        Args:
            sku: SKU instance to update
            sku_code: New SKU code (optional)
            description: New description (optional)

        Returns:
            Updated SKU instance
        """
        if sku_code is not None:
            sku.sku_code = sku_code
        if description is not None:
            sku.description = description

        self.db.commit()
        self.db.refresh(sku)
        return sku

    def delete(self, sku: Sku) -> None:
        """Delete SKU."""
        self.db.delete(sku)
        self.db.commit()

    def list_all(
        self, offset: int = 0, limit: int = 50, search: Optional[str] = None
    ) -> tuple[List[Sku], int]:
        """
        List all SKUs with pagination and optional search.

        Args:
            offset: Number of items to skip
            limit: Maximum items to return
            search: Optional search string to filter by sku_code

        Returns:
            Tuple of (SKU list, total count)
        """
        query = self.db.query(Sku)

        # Apply search filter if provided
        if search:
            query = query.filter(Sku.sku_code.ilike(f"%{search}%"))

        query = query.order_by(Sku.sku_code)
        total = query.count()
        items = query.offset(offset).limit(limit).all()
        return items, total

    def search(self, query: str, limit: int = 10) -> List[Sku]:
        """
        Search SKUs by code for autocomplete.

        Args:
            query: Search string
            limit: Maximum results

        Returns:
            List of matching SKUs
        """
        return (
            self.db.query(Sku)
            .filter(Sku.sku_code.ilike(f"%{query}%"))
            .order_by(Sku.sku_code)
            .limit(limit)
            .all()
        )

    def get_job_count(self, sku_id: int) -> int:
        """Get count of jobs for a SKU using database aggregation."""
        result = (
            self.db.query(func.count(ScrapeJob.id))
            .filter(ScrapeJob.sku_id == sku_id)
            .scalar()
        )
        return result or 0
