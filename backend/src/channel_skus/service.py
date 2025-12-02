# =============================================================================
# Channel SKUs Domain - Business Logic
# =============================================================================
# Purpose: Service layer for Channel SKU operations
# Public API: ChannelSkuService
# Dependencies: sqlalchemy, models, schemas
# =============================================================================

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_

from .models import ChannelSku, ChannelSkuAsinHistory
from ..skus.models import Sku


class ChannelSkuService:
    """
    Service class for Channel SKU business logic.

    Handles CRUD operations, bulk imports, and ASIN history tracking.
    """

    def __init__(self, db: Session):
        self.db = db

    # ===== SKU Resolution =====

    def get_or_create_sku(self, sku_code: str) -> int:
        """
        Get SKU ID by code, or create it if it doesn't exist.

        Args:
            sku_code: SKU code to find or create

        Returns:
            SKU ID
        """
        existing = self.db.query(Sku).filter(Sku.sku_code == sku_code).first()
        if existing:
            return existing.id

        # Create new SKU
        new_sku = Sku(sku_code=sku_code)
        self.db.add(new_sku)
        self.db.flush()  # Get ID without committing
        return new_sku.id

    # ===== Create Operations =====

    def create(
        self,
        channel_sku_code: str,
        marketplace: str,
        current_asin: str,
        sku_id: Optional[int] = None,
        product_title: Optional[str] = None,
    ) -> ChannelSku:
        """
        Create a new Channel SKU.

        Args:
            channel_sku_code: Channel SKU identifier
            marketplace: Amazon marketplace code
            current_asin: Current ASIN mapping
            sku_id: Optional parent SKU ID
            product_title: Optional product title

        Returns:
            Created ChannelSku instance
        """
        channel_sku = ChannelSku(
            channel_sku_code=channel_sku_code,
            marketplace=marketplace,
            current_asin=current_asin,
            sku_id=sku_id,
            product_title=product_title,
        )
        self.db.add(channel_sku)
        self.db.commit()
        self.db.refresh(channel_sku)

        # Record initial ASIN in history
        self._record_asin_history(channel_sku.id, current_asin)

        return channel_sku

    def bulk_create(
        self, items: List[dict]
    ) -> Tuple[int, int, List[str]]:
        """
        Bulk create Channel SKUs, skipping duplicates.

        Args:
            items: List of dicts with channel_sku_code, marketplace, current_asin, sku_code, etc.

        Returns:
            Tuple of (created_count, skipped_count, error_messages)
        """
        created = 0
        skipped = 0
        errors = []

        # Cache for SKU code -> ID mapping to avoid repeated lookups
        sku_cache = {}

        for item in items:
            try:
                # Check for existing
                existing = self.get_by_code_and_marketplace(
                    item["channel_sku_code"], item.get("marketplace", "com")
                )
                if existing:
                    skipped += 1
                    continue

                # Resolve sku_code to sku_id (optional field)
                sku_code = item.get("sku_code")
                sku_id = None
                if sku_code:
                    # Check cache first
                    if sku_code in sku_cache:
                        sku_id = sku_cache[sku_code]
                    else:
                        sku_id = self.get_or_create_sku(sku_code)
                        sku_cache[sku_code] = sku_id

                channel_sku = ChannelSku(
                    channel_sku_code=item["channel_sku_code"],
                    marketplace=item.get("marketplace", "com"),
                    current_asin=item["current_asin"],
                    sku_id=sku_id,
                    product_title=item.get("product_title"),
                )
                self.db.add(channel_sku)
                self.db.flush()  # Get ID without committing

                # Record initial ASIN
                history = ChannelSkuAsinHistory(
                    channel_sku_id=channel_sku.id,
                    asin=item["current_asin"],
                )
                self.db.add(history)
                created += 1

            except Exception as e:
                errors.append(f"{item.get('channel_sku_code', 'unknown')}: {str(e)}")

        self.db.commit()
        return created, skipped, errors

    # ===== Read Operations =====

    def get_by_id(self, channel_sku_id: int) -> Optional[ChannelSku]:
        """Get Channel SKU by ID."""
        return (
            self.db.query(ChannelSku)
            .options(joinedload(ChannelSku.sku))
            .filter(ChannelSku.id == channel_sku_id)
            .first()
        )

    def get_by_code_and_marketplace(
        self, channel_sku_code: str, marketplace: str
    ) -> Optional[ChannelSku]:
        """Get Channel SKU by code and marketplace."""
        return (
            self.db.query(ChannelSku)
            .filter(
                ChannelSku.channel_sku_code == channel_sku_code,
                ChannelSku.marketplace == marketplace,
            )
            .first()
        )

    def list_all(
        self,
        offset: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        marketplace: Optional[str] = None,
        sku_id: Optional[int] = None,
        sku_code: Optional[str] = None,
        min_rating: Optional[float] = None,
        max_rating: Optional[float] = None,
    ) -> Tuple[List[ChannelSku], int]:
        """
        List Channel SKUs with pagination and filters.

        Args:
            offset: Number of items to skip
            limit: Maximum items to return
            search: Search in channel_sku_code or current_asin
            marketplace: Filter by marketplace
            sku_id: Filter by parent SKU ID
            sku_code: Filter by parent SKU code (e.g., "HA-WF2-FLT")
            min_rating: Minimum rating filter
            max_rating: Maximum rating filter

        Returns:
            Tuple of (items list, total count)
        """
        query = self.db.query(ChannelSku).options(joinedload(ChannelSku.sku))

        # Apply filters
        if search:
            query = query.filter(
                or_(
                    ChannelSku.channel_sku_code.ilike(f"%{search}%"),
                    ChannelSku.current_asin.ilike(f"%{search}%"),
                    ChannelSku.product_title.ilike(f"%{search}%"),
                )
            )

        if marketplace:
            query = query.filter(ChannelSku.marketplace == marketplace)

        if sku_id is not None:
            query = query.filter(ChannelSku.sku_id == sku_id)

        if sku_code:
            # Join with Sku table to filter by sku_code
            query = query.join(Sku).filter(Sku.sku_code.ilike(f"%{sku_code}%"))

        if min_rating is not None:
            query = query.filter(ChannelSku.latest_rating >= min_rating)

        if max_rating is not None:
            query = query.filter(ChannelSku.latest_rating <= max_rating)

        query = query.order_by(ChannelSku.channel_sku_code)
        total = query.count()
        items = query.offset(offset).limit(limit).all()

        return items, total

    def search(self, query: str, limit: int = 10) -> List[ChannelSku]:
        """
        Search Channel SKUs for autocomplete.

        Args:
            query: Search string
            limit: Maximum results

        Returns:
            List of matching Channel SKUs
        """
        return (
            self.db.query(ChannelSku)
            .filter(
                or_(
                    ChannelSku.channel_sku_code.ilike(f"%{query}%"),
                    ChannelSku.current_asin.ilike(f"%{query}%"),
                )
            )
            .order_by(ChannelSku.channel_sku_code)
            .limit(limit)
            .all()
        )

    def get_by_ids(self, ids: List[int]) -> List[ChannelSku]:
        """Get multiple Channel SKUs by their IDs."""
        return (
            self.db.query(ChannelSku)
            .filter(ChannelSku.id.in_(ids))
            .all()
        )

    # ===== Update Operations =====

    def update(
        self,
        channel_sku: ChannelSku,
        channel_sku_code: Optional[str] = None,
        marketplace: Optional[str] = None,
        current_asin: Optional[str] = None,
        sku_id: Optional[int] = None,
        product_title: Optional[str] = None,
    ) -> ChannelSku:
        """
        Update Channel SKU fields.

        If current_asin changes, records history entry.
        """
        if channel_sku_code is not None:
            channel_sku.channel_sku_code = channel_sku_code

        if marketplace is not None:
            channel_sku.marketplace = marketplace

        if current_asin is not None and current_asin != channel_sku.current_asin:
            # Record ASIN change in history
            self._record_asin_history(channel_sku.id, current_asin)
            channel_sku.current_asin = current_asin

        if sku_id is not None:
            channel_sku.sku_id = sku_id

        if product_title is not None:
            channel_sku.product_title = product_title

        self.db.commit()
        self.db.refresh(channel_sku)
        return channel_sku

    def update_metrics(
        self,
        channel_sku: ChannelSku,
        rating: Optional[float],
        review_count: Optional[int],
        title: Optional[str] = None,
        scraped_asin: Optional[str] = None,
        job_id: Optional[int] = None,
    ) -> ChannelSku:
        """
        Update metrics from a scan result.

        Checks for ASIN changes and records history.

        Args:
            channel_sku: The Channel SKU to update
            rating: Scraped rating
            review_count: Scraped review count
            title: Scraped product title
            scraped_asin: ASIN returned by Amazon (for change detection)
            job_id: Product scan job ID
        """
        channel_sku.latest_rating = rating
        channel_sku.latest_review_count = review_count
        channel_sku.last_scraped_at = func.current_timestamp()

        if title:
            channel_sku.product_title = title

        # Detect ASIN change
        if scraped_asin and scraped_asin != channel_sku.current_asin:
            self._record_asin_history(channel_sku.id, scraped_asin, job_id)
            channel_sku.current_asin = scraped_asin

        self.db.commit()
        self.db.refresh(channel_sku)
        return channel_sku

    # ===== Delete Operations =====

    def delete(self, channel_sku: ChannelSku) -> None:
        """Delete Channel SKU (cascades to history and scan items)."""
        self.db.delete(channel_sku)
        self.db.commit()

    # ===== History Operations =====

    def _record_asin_history(
        self,
        channel_sku_id: int,
        asin: str,
        job_id: Optional[int] = None,
    ) -> None:
        """Record an ASIN in the history table."""
        history = ChannelSkuAsinHistory(
            channel_sku_id=channel_sku_id,
            asin=asin,
            changed_by_job_id=job_id,
        )
        self.db.add(history)

    def get_asin_history(
        self, channel_sku_id: int, limit: int = 50
    ) -> List[ChannelSkuAsinHistory]:
        """Get ASIN change history for a Channel SKU."""
        return (
            self.db.query(ChannelSkuAsinHistory)
            .filter(ChannelSkuAsinHistory.channel_sku_id == channel_sku_id)
            .order_by(ChannelSkuAsinHistory.changed_at.desc())
            .limit(limit)
            .all()
        )

    # ===== Aggregation Operations =====

    def get_marketplace_counts(self) -> dict:
        """Get count of Channel SKUs per marketplace."""
        results = (
            self.db.query(
                ChannelSku.marketplace,
                func.count(ChannelSku.id).label("count"),
            )
            .group_by(ChannelSku.marketplace)
            .all()
        )
        return {row.marketplace: row.count for row in results}

    def get_rating_distribution(self) -> dict:
        """Get distribution of ratings across all Channel SKUs."""
        results = (
            self.db.query(
                func.floor(ChannelSku.latest_rating).label("rating_floor"),
                func.count(ChannelSku.id).label("count"),
            )
            .filter(ChannelSku.latest_rating.isnot(None))
            .group_by(func.floor(ChannelSku.latest_rating))
            .all()
        )
        return {int(row.rating_floor): row.count for row in results}

    def get_total_count(self) -> int:
        """Get total count of Channel SKUs."""
        return self.db.query(func.count(ChannelSku.id)).scalar() or 0

    def get_scan_history(
        self, channel_sku_id: int, limit: int = 50
    ) -> List[dict]:
        """
        Get scan history (rating/review changes over time) for a Channel SKU.

        Returns list of dicts with job_id, job_name, scraped_at, rating, review_count, scraped_asin.
        """
        # Lazy import to avoid circular dependency
        from ..product_scans.models import ProductScanItem, ProductScanJob

        results = (
            self.db.query(
                ProductScanItem.job_id,
                ProductScanJob.job_name,
                ProductScanItem.completed_at,
                ProductScanItem.scraped_rating,
                ProductScanItem.scraped_review_count,
                ProductScanItem.scraped_asin,
            )
            .join(ProductScanJob, ProductScanItem.job_id == ProductScanJob.id)
            .filter(ProductScanItem.channel_sku_id == channel_sku_id)
            .filter(ProductScanItem.status == "completed")
            .order_by(ProductScanItem.completed_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "job_id": row.job_id,
                "job_name": row.job_name,
                "scraped_at": row.completed_at,
                "rating": row.scraped_rating,
                "review_count": row.scraped_review_count,
                "scraped_asin": row.scraped_asin,
            }
            for row in results
        ]
