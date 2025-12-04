# =============================================================================
# Competitors Domain - Service Layer
# =============================================================================
# Purpose: Business logic for competitor tracking and research
# Public API: CompetitorService
# Dependencies: sqlalchemy, models, schemas
# =============================================================================

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Tuple, Any
import logging
import json

from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import Session, joinedload, subqueryload


from .models import (
    Competitor,
    CompetitorData,
    CompetitorPriceHistory,
    CompetitorKeyword,
    KeywordChannelSkuLink,
    KeywordCompetitorLink,
    CompetitorScrapeJob,
    CompetitorScrapeItem,
)
from .schemas import (
    CompetitorCreate,
    CompetitorUpdate,
    CompetitorScheduleUpdate,
    KeywordCreate,
    KeywordUpdate,
    ScrapeJobCreate,
    ScheduleType,
)
from ..skus.models import Sku
from ..channel_skus.models import ChannelSku
from ..pagination import paginate

logger = logging.getLogger(__name__)


def _serialize_json(val):
    """Serialize dict/list to JSON string for PyMySQL compatibility."""
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return json.dumps(val, ensure_ascii=False, default=str)
    return val


class CompetitorService:
    """Service class for competitor operations."""

    # =========================================================================
    # Competitor CRUD
    # =========================================================================

    @staticmethod
    def create(db: Session, data: CompetitorCreate) -> Competitor:
        """Create a new competitor."""
        competitor = Competitor(
            sku_id=data.sku_id,
            asin=data.asin.upper(),
            marketplace=data.marketplace.lower(),
            pack_size=data.pack_size or 1,
            display_name=data.display_name,
            schedule=data.schedule.value,
            notes=data.notes,
        )
        if data.schedule != ScheduleType.NONE:
            competitor.next_scrape_at = CompetitorService._calculate_next_scrape(
                data.schedule
            )
        db.add(competitor)
        db.commit()
        db.refresh(competitor)
        return competitor

    @staticmethod
    def bulk_create(
        db: Session, items: List[CompetitorCreate]
    ) -> Tuple[int, int, List[str]]:
        """Bulk create competitors. Returns (created, skipped, errors)."""
        created = 0
        skipped = 0
        errors = []

        for item in items:
            try:
                # Check if already exists for this specific SKU
                existing = (
                    db.query(Competitor)
                    .filter(
                        Competitor.asin == item.asin.upper(),
                        Competitor.marketplace == item.marketplace.lower(),
                        Competitor.sku_id == item.sku_id,
                    )
                    .first()
                )
                if existing:
                    skipped += 1
                    continue

                CompetitorService.create(db, item)
                created += 1
            except Exception as e:
                errors.append(f"{item.asin}: {str(e)}")
                db.rollback()

        return created, skipped, errors

    @staticmethod
    def get_by_id(db: Session, competitor_id: int) -> Optional[Competitor]:
        """Get competitor by ID with related data."""
        return (
            db.query(Competitor)
            .options(joinedload(Competitor.sku), joinedload(Competitor.data))
            .filter(Competitor.id == competitor_id)
            .first()
        )

    @staticmethod
    def list_all(
        db: Session,
        page: int = 1,
        per_page: int = 50,
        sku_id: Optional[int] = None,
        marketplace: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Competitor], int]:
        """List competitors with filtering and pagination."""
        query = db.query(Competitor).options(
            joinedload(Competitor.sku), joinedload(Competitor.data)
        )

        # Apply filters
        if sku_id is not None:
            query = query.filter(Competitor.sku_id == sku_id)
        if marketplace:
            query = query.filter(Competitor.marketplace == marketplace.lower())
        if is_active is not None:
            query = query.filter(Competitor.is_active == is_active)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Competitor.asin.ilike(search_term),
                    Competitor.display_name.ilike(search_term),
                )
            )

        # Order by created_at desc
        query = query.order_by(desc(Competitor.created_at))

        return paginate(query, page, per_page)

    @staticmethod
    def update(
        db: Session, competitor: Competitor, data: CompetitorUpdate
    ) -> Competitor:
        """Update a competitor."""
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "schedule" and value is not None:
                value = value.value
                # Recalculate next scrape time
                if value != "none":
                    competitor.next_scrape_at = (
                        CompetitorService._calculate_next_scrape(ScheduleType(value))
                    )
                else:
                    competitor.next_scrape_at = None
            setattr(competitor, field, value)

        db.commit()
        db.refresh(competitor)
        return competitor

    @staticmethod
    def update_schedule(
        db: Session, competitor: Competitor, data: CompetitorScheduleUpdate
    ) -> Competitor:
        """Update competitor schedule."""
        competitor.schedule = data.schedule.value
        if data.schedule != ScheduleType.NONE:
            competitor.next_scrape_at = CompetitorService._calculate_next_scrape(
                data.schedule
            )
        else:
            competitor.next_scrape_at = None
        db.commit()
        db.refresh(competitor)
        return competitor

    @staticmethod
    def delete(db: Session, competitor: Competitor) -> None:
        """Delete a competitor."""
        db.delete(competitor)
        db.commit()

    # =========================================================================
    # Competitor Data Operations
    # =========================================================================

    @staticmethod
    def save_scraped_data(
        db: Session, competitor_id: int, parsed_data: dict
    ) -> CompetitorData:
        """Save or update scraped data for a competitor."""
        # Get competitor for pack_size
        competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
        if not competitor:
            raise ValueError(f"Competitor {competitor_id} not found")

        # Calculate unit price
        price = parsed_data.get("price")
        pack_size = competitor.pack_size or 1
        unit_price = None
        if price is not None and pack_size > 0:
            unit_price = Decimal(str(price)) / pack_size

        # Check for existing data
        existing = (
            db.query(CompetitorData)
            .filter(CompetitorData.competitor_id == competitor_id)
            .first()
        )

        # Debug: log types of all fields
        for key, val in parsed_data.items():
            if isinstance(val, (dict, list)):
                logger.warning(f"Field '{key}' is {type(val).__name__}: {str(val)[:100]}")

        data_fields = {
            "title": parsed_data.get("title"),
            "brand": parsed_data.get("brand"),
            "manufacturer": parsed_data.get("manufacturer"),
            "price": price,
            "retail_price": parsed_data.get("retail_price"),
            "shipping_price": parsed_data.get("shipping_price"),
            "currency": parsed_data.get("currency"),
            "unit_price": unit_price,
            "price_saving": _serialize_json(parsed_data.get("price_saving")),
            "rating": parsed_data.get("rating"),
            "review_count": parsed_data.get("review_count"),
            "past_sales": parsed_data.get("past_sales"),
            "availability": parsed_data.get("availability"),
            "sold_by": parsed_data.get("sold_by"),
            "fulfilled_by": parsed_data.get("fulfilled_by"),
            "seller_id": parsed_data.get("seller_id"),
            "is_prime": parsed_data.get("is_prime", False),
            "features": _serialize_json(parsed_data.get("features")),
            "product_description": parsed_data.get("product_description"),
            "main_image_url": parsed_data.get("main_image_url"),
            "images": _serialize_json(parsed_data.get("images")),
            "videos": _serialize_json(parsed_data.get("videos")),
            "categories": _serialize_json(parsed_data.get("categories")),
            "variations": _serialize_json(parsed_data.get("variations")),
            "variations_count": parsed_data.get("variations_count", 0),
            "product_details": _serialize_json(parsed_data.get("product_details")),
            "review_insights": _serialize_json(parsed_data.get("review_insights")),
            "raw_data": _serialize_json(parsed_data.get("raw_data")),
            "scraped_at": datetime.utcnow(),
        }

        if existing:
            for field, value in data_fields.items():
                setattr(existing, field, value)
            db.commit()
            db.refresh(existing)
            return existing
        else:
            new_data = CompetitorData(competitor_id=competitor_id, **data_fields)
            db.add(new_data)
            db.commit()
            db.refresh(new_data)
            return new_data

    @staticmethod
    def record_price_history(db: Session, competitor_id: int) -> None:
        """Record current price data to history table."""
        # Get current data
        data = (
            db.query(CompetitorData)
            .filter(CompetitorData.competitor_id == competitor_id)
            .first()
        )
        if not data:
            return

        history = CompetitorPriceHistory(
            competitor_id=competitor_id,
            price=data.price,
            unit_price=data.unit_price,
            shipping_price=data.shipping_price,
            availability=data.availability,
            rating=data.rating,
            review_count=data.review_count,
        )
        db.add(history)
        db.commit()

    @staticmethod
    def get_price_history(
        db: Session,
        competitor_id: int,
        page: int = 1,
        per_page: int = 50,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Tuple[List[CompetitorPriceHistory], int]:
        """Get price history for a competitor."""
        query = db.query(CompetitorPriceHistory).filter(
            CompetitorPriceHistory.competitor_id == competitor_id
        )

        if start_date:
            query = query.filter(CompetitorPriceHistory.scraped_at >= start_date)
        if end_date:
            query = query.filter(CompetitorPriceHistory.scraped_at <= end_date)

        query = query.order_by(desc(CompetitorPriceHistory.scraped_at))

        return paginate(query, page, per_page)

    # =========================================================================
    # Keyword Operations
    # =========================================================================

    @staticmethod
    def create_keyword(db: Session, data: KeywordCreate) -> CompetitorKeyword:
        """Create a new keyword."""
        keyword = CompetitorKeyword(
            sku_id=data.sku_id,
            keyword=data.keyword,
            marketplace=data.marketplace.lower(),
            notes=data.notes,
        )
        db.add(keyword)
        db.commit()
        db.refresh(keyword)
        return keyword

    @staticmethod
    def get_keyword_by_id(db: Session, keyword_id: int) -> Optional[CompetitorKeyword]:
        """Get keyword by ID."""
        return (
            db.query(CompetitorKeyword)
            .options(joinedload(CompetitorKeyword.sku))
            .filter(CompetitorKeyword.id == keyword_id)
            .first()
        )

    @staticmethod
    def list_keywords(
        db: Session,
        page: int = 1,
        per_page: int = 50,
        sku_id: Optional[int] = None,
        marketplace: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[CompetitorKeyword], int]:
        """List keywords with filtering."""
        # Use subqueryload for relationships to avoid N+1 queries when counting links
        query = db.query(CompetitorKeyword).options(
            joinedload(CompetitorKeyword.sku),
            subqueryload(CompetitorKeyword.channel_sku_links),
            subqueryload(CompetitorKeyword.competitor_links),
        )

        if sku_id is not None:
            query = query.filter(CompetitorKeyword.sku_id == sku_id)
        if marketplace:
            query = query.filter(CompetitorKeyword.marketplace == marketplace.lower())
        if search:
            query = query.filter(CompetitorKeyword.keyword.ilike(f"%{search}%"))

        query = query.order_by(desc(CompetitorKeyword.created_at))

        return paginate(query, page, per_page)

    @staticmethod
    def update_keyword(
        db: Session, keyword: CompetitorKeyword, data: KeywordUpdate
    ) -> CompetitorKeyword:
        """Update a keyword."""
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "marketplace" and value:
                value = value.lower()
            setattr(keyword, field, value)
        db.commit()
        db.refresh(keyword)
        return keyword

    @staticmethod
    def delete_keyword(db: Session, keyword: CompetitorKeyword) -> None:
        """Delete a keyword."""
        db.delete(keyword)
        db.commit()

    @staticmethod
    def link_channel_sku_to_keyword(
        db: Session, keyword_id: int, channel_sku_id: int
    ) -> KeywordChannelSkuLink:
        """Link a channel SKU to a keyword."""
        link = KeywordChannelSkuLink(
            keyword_id=keyword_id, channel_sku_id=channel_sku_id
        )
        db.add(link)
        db.commit()
        db.refresh(link)
        return link

    @staticmethod
    def unlink_channel_sku_from_keyword(
        db: Session, keyword_id: int, channel_sku_id: int
    ) -> bool:
        """Unlink a channel SKU from a keyword."""
        deleted = (
            db.query(KeywordChannelSkuLink)
            .filter(
                KeywordChannelSkuLink.keyword_id == keyword_id,
                KeywordChannelSkuLink.channel_sku_id == channel_sku_id,
            )
            .delete()
        )
        db.commit()
        return deleted > 0

    @staticmethod
    def link_competitor_to_keyword(
        db: Session, keyword_id: int, competitor_id: int
    ) -> KeywordCompetitorLink:
        """Link a competitor to a keyword."""
        link = KeywordCompetitorLink(keyword_id=keyword_id, competitor_id=competitor_id)
        db.add(link)
        db.commit()
        db.refresh(link)
        return link

    @staticmethod
    def unlink_competitor_from_keyword(
        db: Session, keyword_id: int, competitor_id: int
    ) -> bool:
        """Unlink a competitor from a keyword."""
        deleted = (
            db.query(KeywordCompetitorLink)
            .filter(
                KeywordCompetitorLink.keyword_id == keyword_id,
                KeywordCompetitorLink.competitor_id == competitor_id,
            )
            .delete()
        )
        db.commit()
        return deleted > 0

    # =========================================================================
    # Scrape Job Operations
    # =========================================================================

    @staticmethod
    def create_scrape_job(db: Session, data: ScrapeJobCreate) -> CompetitorScrapeJob:
        """Create a new competitor scrape job."""
        job = CompetitorScrapeJob(
            job_name=data.job_name,
            marketplace=data.marketplace.lower(),
            total_competitors=len(data.competitor_ids),
        )
        db.add(job)
        db.flush()

        # Create items for each competitor
        for comp_id in data.competitor_ids:
            competitor = (
                db.query(Competitor).filter(Competitor.id == comp_id).first()
            )
            if competitor:
                item = CompetitorScrapeItem(
                    job_id=job.id,
                    competitor_id=comp_id,
                    input_asin=competitor.asin,
                )
                db.add(item)

        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_scrape_job_by_id(
        db: Session, job_id: int
    ) -> Optional[CompetitorScrapeJob]:
        """Get scrape job by ID with items."""
        return (
            db.query(CompetitorScrapeJob)
            .options(joinedload(CompetitorScrapeJob.items))
            .filter(CompetitorScrapeJob.id == job_id)
            .first()
        )

    @staticmethod
    def list_scrape_jobs(
        db: Session,
        page: int = 1,
        per_page: int = 50,
        status: Optional[str] = None,
    ) -> Tuple[List[CompetitorScrapeJob], int]:
        """List scrape jobs."""
        query = db.query(CompetitorScrapeJob)

        if status:
            query = query.filter(CompetitorScrapeJob.status == status)

        query = query.order_by(desc(CompetitorScrapeJob.created_at))

        return paginate(query, page, per_page)

    @staticmethod
    def get_next_queued_job(db: Session) -> Optional[CompetitorScrapeJob]:
        """Get the next queued job for processing."""
        return (
            db.query(CompetitorScrapeJob)
            .filter(CompetitorScrapeJob.status == "queued")
            .order_by(CompetitorScrapeJob.created_at)
            .first()
        )

    @staticmethod
    def get_pending_items_for_job(
        db: Session, job_id: int
    ) -> List[CompetitorScrapeItem]:
        """Get pending items for a job."""
        return (
            db.query(CompetitorScrapeItem)
            .filter(
                CompetitorScrapeItem.job_id == job_id,
                CompetitorScrapeItem.status == "pending",
            )
            .all()
        )

    @staticmethod
    def cancel_scrape_job(db: Session, job: CompetitorScrapeJob) -> None:
        """Cancel a scrape job."""
        job.status = "cancelled"
        # Cancel all pending items
        db.query(CompetitorScrapeItem).filter(
            CompetitorScrapeItem.job_id == job.id,
            CompetitorScrapeItem.status == "pending",
        ).update({"status": "failed", "error_message": "Job cancelled"})
        db.commit()

    # =========================================================================
    # Scheduling Operations
    # =========================================================================

    @staticmethod
    def get_due_scheduled_competitors(db: Session) -> List[Competitor]:
        """Get competitors due for scheduled scraping."""
        now = datetime.utcnow()
        return (
            db.query(Competitor)
            .filter(
                Competitor.is_active == True,
                Competitor.schedule != "none",
                Competitor.next_scrape_at <= now,
            )
            .all()
        )

    @staticmethod
    def update_next_scrape(db: Session, competitor: Competitor) -> None:
        """Update the next scrape time after successful scrape."""
        schedule = ScheduleType(competitor.schedule)
        if schedule != ScheduleType.NONE:
            competitor.next_scrape_at = CompetitorService._calculate_next_scrape(
                schedule
            )
            db.commit()

    @staticmethod
    def _calculate_next_scrape(schedule: ScheduleType) -> datetime:
        """Calculate the next scrape time based on schedule."""
        now = datetime.utcnow()
        if schedule == ScheduleType.DAILY:
            return now + timedelta(days=1)
        elif schedule == ScheduleType.EVERY_2_DAYS:
            return now + timedelta(days=2)
        elif schedule == ScheduleType.EVERY_3_DAYS:
            return now + timedelta(days=3)
        elif schedule == ScheduleType.WEEKLY:
            return now + timedelta(weeks=1)
        elif schedule == ScheduleType.MONTHLY:
            return now + timedelta(days=30)
        return now

    # =========================================================================
    # Dashboard & Stats
    # =========================================================================

    @staticmethod
    def get_global_stats(db: Session) -> dict:
        """Get global dashboard statistics."""
        total = db.query(func.count(Competitor.id)).scalar() or 0
        active = (
            db.query(func.count(Competitor.id))
            .filter(Competitor.is_active == True)
            .scalar()
            or 0
        )
        keywords = db.query(func.count(CompetitorKeyword.id)).scalar() or 0

        # Parent SKUs with competitors
        parent_skus = (
            db.query(func.count(func.distinct(Competitor.sku_id)))
            .filter(Competitor.sku_id.isnot(None))
            .scalar()
            or 0
        )

        # By marketplace
        marketplace_counts = (
            db.query(Competitor.marketplace, func.count(Competitor.id))
            .group_by(Competitor.marketplace)
            .all()
        )
        by_marketplace = {mp: count for mp, count in marketplace_counts}

        # Recent price changes (last 7 days with actual price differences)
        # Get history entries with their competitor info and compare to previous entry
        recent_price_changes = []

        # Get recent history entries with competitor joins
        history_entries = (
            db.query(
                CompetitorPriceHistory,
                Competitor.asin,
                Competitor.sku_id,
                Sku.sku_code,
            )
            .join(Competitor, CompetitorPriceHistory.competitor_id == Competitor.id)
            .outerjoin(Sku, Competitor.sku_id == Sku.id)
            .filter(
                CompetitorPriceHistory.scraped_at
                >= datetime.utcnow() - timedelta(days=7)
            )
            .order_by(desc(CompetitorPriceHistory.scraped_at))
            .limit(50)  # Get more to find actual changes
            .all()
        )

        # For each entry, find the previous entry to compare prices
        seen_competitors = set()
        for entry, asin, sku_id, sku_code in history_entries:
            if entry.competitor_id in seen_competitors:
                continue

            # Get previous entry for this competitor
            prev_entry = (
                db.query(CompetitorPriceHistory)
                .filter(
                    CompetitorPriceHistory.competitor_id == entry.competitor_id,
                    CompetitorPriceHistory.id < entry.id
                )
                .order_by(desc(CompetitorPriceHistory.id))
                .first()
            )

            # Only include if there's a price change
            if prev_entry and entry.price and prev_entry.price:
                if entry.price != prev_entry.price:
                    recent_price_changes.append({
                        "competitor_id": entry.competitor_id,
                        "competitor_asin": asin,
                        "sku_code": sku_code,
                        "old_price": prev_entry.price,
                        "new_price": entry.price,
                        "currency": "USD",  # TODO: Get from competitor data
                        "recorded_at": entry.scraped_at,
                    })
                    seen_competitors.add(entry.competitor_id)

            if len(recent_price_changes) >= 10:
                break

        # Upcoming scrapes
        upcoming = (
            db.query(Competitor)
            .filter(
                Competitor.is_active == True,
                Competitor.schedule != "none",
                Competitor.next_scrape_at.isnot(None),
            )
            .order_by(Competitor.next_scrape_at)
            .limit(10)
            .all()
        )

        return {
            "total_competitors": total,
            "active_competitors": active,
            "total_keywords": keywords,
            "total_parent_skus": parent_skus,
            "competitors_by_marketplace": by_marketplace,
            "recent_price_changes": recent_price_changes,
            "upcoming_scrapes": upcoming,
        }

    @staticmethod
    def get_parent_sku_stats(db: Session, sku_id: int) -> Optional[dict]:
        """Get statistics for a specific parent SKU."""
        sku = db.query(Sku).filter(Sku.id == sku_id).first()
        if not sku:
            return None

        # Get competitors
        competitors = (
            db.query(Competitor)
            .options(joinedload(Competitor.data))
            .filter(Competitor.sku_id == sku_id)
            .all()
        )

        # Get keywords
        keywords = (
            db.query(CompetitorKeyword)
            .filter(CompetitorKeyword.sku_id == sku_id)
            .all()
        )

        # Get channel SKUs
        channel_skus_count = (
            db.query(func.count(ChannelSku.id))
            .filter(ChannelSku.sku_id == sku_id)
            .scalar()
            or 0
        )

        # Calculate price stats from competitor data
        prices = [c.data.price for c in competitors if c.data and c.data.price]
        ratings = [c.data.rating for c in competitors if c.data and c.data.rating]

        return {
            "sku_id": sku.id,
            "sku_code": sku.sku_code,
            "display_name": sku.display_name,
            "total_competitors": len(competitors),
            "total_keywords": len(keywords),
            "total_channel_skus": channel_skus_count,
            "avg_competitor_price": sum(prices) / len(prices) if prices else None,
            "min_competitor_price": min(prices) if prices else None,
            "max_competitor_price": max(prices) if prices else None,
            "avg_competitor_rating": sum(ratings) / len(ratings) if ratings else None,
            "competitors": competitors,
            "keywords": keywords,
        }

    @staticmethod
    def list_parent_skus_with_stats(
        db: Session, page: int = 1, per_page: int = 50
    ) -> Tuple[List[dict], int]:
        """List parent SKUs that have competitors with stats."""
        # Get SKUs that have competitors
        subquery = (
            db.query(Competitor.sku_id)
            .filter(Competitor.sku_id.isnot(None))
            .distinct()
            .subquery()
        )

        query = db.query(Sku).filter(Sku.id.in_(db.query(subquery.c.sku_id)))
        total = query.count()

        skus = query.offset((page - 1) * per_page).limit(per_page).all()

        # Get stats for each SKU
        result = []
        for sku in skus:
            stats = CompetitorService.get_parent_sku_stats(db, sku.id)
            if stats:
                result.append(stats)

        return result, total
