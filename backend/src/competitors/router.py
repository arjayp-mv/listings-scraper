# =============================================================================
# Competitors Domain - FastAPI Router
# =============================================================================
# Purpose: API endpoints for competitor tracking and research
# Public API: router
# Dependencies: fastapi, service, schemas
# =============================================================================

import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..pagination import calculate_pages
from .dependencies import valid_competitor, valid_keyword, valid_scrape_job
from .models import Competitor, CompetitorKeyword, CompetitorScrapeJob
from .schemas import (
    CompetitorCreate,
    CompetitorBulkCreate,
    CompetitorUpdate,
    CompetitorScheduleUpdate,
    CompetitorResponse,
    CompetitorListResponse,
    CompetitorDetailResponse,
    KeywordCreate,
    KeywordUpdate,
    KeywordResponse,
    KeywordListResponse,
    KeywordDetailResponse,
    ScrapeJobCreate,
    ScrapeJobResponse,
    ScrapeJobListResponse,
    ScrapeJobDetailResponse,
    PriceHistoryResponse,
    PriceHistoryListResponse,
    PriceChangeResponse,
    DashboardStats,
    ParentSkuStats,
    ParentSkuListResponse,
)
from .service import CompetitorService

router = APIRouter(prefix="/api/competitors", tags=["Competitors"])


# =============================================================================
# Dashboard & Stats Endpoints (MUST be before /{competitor_id} routes)
# =============================================================================


@router.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get global dashboard statistics."""
    stats = CompetitorService.get_global_stats(db)

    # Convert objects to serializable format
    return DashboardStats(
        total_competitors=stats["total_competitors"],
        active_competitors=stats["active_competitors"],
        total_keywords=stats["total_keywords"],
        total_parent_skus=stats["total_parent_skus"],
        competitors_by_marketplace=stats["competitors_by_marketplace"],
        recent_price_changes=stats["recent_price_changes"],  # Already dict format
        upcoming_scrapes=[
            _competitor_to_response(c).model_dump()
            for c in stats["upcoming_scrapes"]
        ],
    )


@router.get("/dashboard/by-sku/{sku_id}", response_model=ParentSkuStats)
def get_sku_stats(sku_id: int, db: Session = Depends(get_db)):
    """Get statistics for a specific parent SKU."""
    stats = CompetitorService.get_parent_sku_stats(db, sku_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SKU with ID {sku_id} not found",
        )

    return ParentSkuStats(
        sku_id=stats["sku_id"],
        sku_code=stats["sku_code"],
        display_name=stats["display_name"],
        total_competitors=stats["total_competitors"],
        total_keywords=stats["total_keywords"],
        total_channel_skus=stats["total_channel_skus"],
        avg_competitor_price=stats["avg_competitor_price"],
        min_competitor_price=stats["min_competitor_price"],
        max_competitor_price=stats["max_competitor_price"],
        avg_competitor_rating=stats["avg_competitor_rating"],
        competitors=[_competitor_to_response(c) for c in stats["competitors"]],
        keywords=[_keyword_to_response(k) for k in stats["keywords"]],
    )


@router.get("/parent-skus", response_model=ParentSkuListResponse)
def list_parent_skus(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List parent SKUs with competitor stats."""
    items, total = CompetitorService.list_parent_skus_with_stats(db, page, per_page)

    return ParentSkuListResponse(
        items=[
            ParentSkuStats(
                sku_id=s["sku_id"],
                sku_code=s["sku_code"],
                display_name=s["display_name"],
                total_competitors=s["total_competitors"],
                total_keywords=s["total_keywords"],
                total_channel_skus=s["total_channel_skus"],
                avg_competitor_price=s["avg_competitor_price"],
                min_competitor_price=s["min_competitor_price"],
                max_competitor_price=s["max_competitor_price"],
                avg_competitor_rating=s["avg_competitor_rating"],
            )
            for s in items
        ],
        total=total,
        page=page,
        per_page=per_page,
        pages=calculate_pages(total, per_page),
    )


# =============================================================================
# Keyword Endpoints (MUST be before /{competitor_id} routes)
# =============================================================================


@router.get("/keywords", response_model=KeywordListResponse)
def list_keywords(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    sku_id: Optional[int] = None,
    marketplace: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all keywords."""
    items, total = CompetitorService.list_keywords(
        db,
        page=page,
        per_page=per_page,
        sku_id=sku_id,
        marketplace=marketplace,
        search=search,
    )

    return KeywordListResponse(
        items=[_keyword_to_response(k) for k in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=calculate_pages(total, per_page),
    )


@router.post(
    "/keywords", response_model=KeywordResponse, status_code=status.HTTP_201_CREATED
)
def create_keyword(data: KeywordCreate, db: Session = Depends(get_db)):
    """Create a new keyword."""
    keyword = CompetitorService.create_keyword(db, data)
    return _keyword_to_response(keyword)


@router.get("/keywords/{keyword_id}", response_model=KeywordDetailResponse)
def get_keyword(keyword: CompetitorKeyword = Depends(valid_keyword)):
    """Get keyword details with linked items."""
    return _keyword_to_detail_response(keyword)


@router.put("/keywords/{keyword_id}", response_model=KeywordResponse)
def update_keyword(
    data: KeywordUpdate,
    keyword: CompetitorKeyword = Depends(valid_keyword),
    db: Session = Depends(get_db),
):
    """Update a keyword."""
    updated = CompetitorService.update_keyword(db, keyword, data)
    return _keyword_to_response(updated)


@router.delete("/keywords/{keyword_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_keyword(
    keyword: CompetitorKeyword = Depends(valid_keyword),
    db: Session = Depends(get_db),
):
    """Delete a keyword."""
    CompetitorService.delete_keyword(db, keyword)


@router.post(
    "/keywords/{keyword_id}/channel-skus/{channel_sku_id}",
    status_code=status.HTTP_201_CREATED,
)
def link_channel_sku_to_keyword(
    channel_sku_id: int,
    keyword: CompetitorKeyword = Depends(valid_keyword),
    db: Session = Depends(get_db),
):
    """Link a channel SKU to a keyword."""
    try:
        CompetitorService.link_channel_sku_to_keyword(db, keyword.id, channel_sku_id)
        return {"message": "Channel SKU linked successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/keywords/{keyword_id}/channel-skus/{channel_sku_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unlink_channel_sku_from_keyword(
    channel_sku_id: int,
    keyword: CompetitorKeyword = Depends(valid_keyword),
    db: Session = Depends(get_db),
):
    """Unlink a channel SKU from a keyword."""
    CompetitorService.unlink_channel_sku_from_keyword(db, keyword.id, channel_sku_id)


@router.post(
    "/keywords/{keyword_id}/competitors/{competitor_id}",
    status_code=status.HTTP_201_CREATED,
)
def link_competitor_to_keyword(
    competitor_id: int,
    keyword: CompetitorKeyword = Depends(valid_keyword),
    db: Session = Depends(get_db),
):
    """Link a competitor to a keyword."""
    try:
        CompetitorService.link_competitor_to_keyword(db, keyword.id, competitor_id)
        return {"message": "Competitor linked successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/keywords/{keyword_id}/competitors/{competitor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unlink_competitor_from_keyword(
    competitor_id: int,
    keyword: CompetitorKeyword = Depends(valid_keyword),
    db: Session = Depends(get_db),
):
    """Unlink a competitor from a keyword."""
    CompetitorService.unlink_competitor_from_keyword(db, keyword.id, competitor_id)


# =============================================================================
# Scrape Job Endpoints (MUST be before /{competitor_id} routes)
# =============================================================================


@router.get("/scrape-jobs", response_model=ScrapeJobListResponse)
def list_scrape_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    """List competitor scrape jobs."""
    items, total = CompetitorService.list_scrape_jobs(
        db, page=page, per_page=per_page, status=status_filter
    )

    return ScrapeJobListResponse(
        items=[ScrapeJobResponse.model_validate(j) for j in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=calculate_pages(total, per_page),
    )


@router.post(
    "/scrape-jobs", response_model=ScrapeJobResponse, status_code=status.HTTP_201_CREATED
)
def create_scrape_job(data: ScrapeJobCreate, db: Session = Depends(get_db)):
    """Create a new competitor scrape job.

    Can provide either competitor_ids directly, or sku_id to scrape all competitors
    for that SKU.
    """
    # If sku_id is provided but no competitor_ids, get all competitors for that SKU
    if data.sku_id and not data.competitor_ids:
        competitors = db.query(Competitor).filter(
            Competitor.sku_id == data.sku_id,
            Competitor.is_active == True,
        ).all()

        if not competitors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No active competitors found for SKU ID {data.sku_id}",
            )

        data.competitor_ids = [c.id for c in competitors]
        # Use first competitor's marketplace if not specified
        if not data.marketplace or data.marketplace == "com":
            data.marketplace = competitors[0].marketplace

    if not data.competitor_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either competitor_ids or sku_id is required",
        )

    job = CompetitorService.create_scrape_job(db, data)
    return ScrapeJobResponse.model_validate(job)


@router.get("/scrape-jobs/{job_id}", response_model=ScrapeJobDetailResponse)
def get_scrape_job(job: CompetitorScrapeJob = Depends(valid_scrape_job)):
    """Get scrape job details with items."""
    return _scrape_job_to_detail_response(job)


@router.post("/scrape-jobs/{job_id}/cancel", status_code=status.HTTP_200_OK)
def cancel_scrape_job(
    job: CompetitorScrapeJob = Depends(valid_scrape_job),
    db: Session = Depends(get_db),
):
    """Cancel a scrape job."""
    if job.status not in ["queued", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel queued or running jobs",
        )
    CompetitorService.cancel_scrape_job(db, job)
    return {"message": "Job cancelled"}


# =============================================================================
# Export Endpoints (MUST be before /{competitor_id} routes)
# =============================================================================


@router.get("/export/csv")
def export_competitors_csv(
    marketplace: Optional[str] = None,
    sku_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Export competitors to CSV."""
    items, _ = CompetitorService.list_all(
        db, page=1, per_page=10000, marketplace=marketplace, sku_id=sku_id
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "ASIN",
            "Marketplace",
            "Display Name",
            "Parent SKU",
            "Pack Size",
            "Price",
            "Unit Price",
            "Rating",
            "Review Count",
            "Schedule",
            "Active",
        ]
    )

    for comp in items:
        writer.writerow(
            [
                comp.asin,
                comp.marketplace,
                comp.display_name or "",
                comp.sku.sku_code if comp.sku else "",
                comp.pack_size or 1,
                comp.data.price if comp.data else "",
                comp.data.unit_price if comp.data else "",
                comp.data.rating if comp.data else "",
                comp.data.review_count if comp.data else "",
                comp.schedule,
                "Yes" if comp.is_active else "No",
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=competitors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        },
    )


@router.get("/export/price-changer")
def export_for_price_changer(
    marketplace: Optional[str] = None,
    sku_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Export competitors in format for price changer tool."""
    items, _ = CompetitorService.list_all(
        db,
        page=1,
        per_page=10000,
        marketplace=marketplace,
        sku_id=sku_id,
        is_active=True,
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "ASIN",
            "Marketplace",
            "Competitor Name",
            "Parent SKU",
            "Price",
            "Unit Price",
            "Pack Size",
            "Rating",
            "Review Count",
            "Availability",
            "Scraped At",
        ]
    )

    for comp in items:
        writer.writerow(
            [
                comp.asin,
                comp.marketplace,
                comp.display_name or comp.asin,
                comp.sku.sku_code if comp.sku else "",
                comp.data.price if comp.data else "",
                comp.data.unit_price if comp.data else "",
                comp.pack_size or 1,
                comp.data.rating if comp.data else "",
                comp.data.review_count if comp.data else "",
                comp.data.availability if comp.data else "",
                comp.data.scraped_at.isoformat() if comp.data else "",
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=price_changer_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        },
    )


# =============================================================================
# Competitor CRUD Endpoints (/{competitor_id} routes MUST be last)
# =============================================================================


@router.get("")
def list_competitors(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    sku_id: Optional[int] = None,
    marketplace: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    include_data: bool = Query(False, description="Include scraped data in response"),
    db: Session = Depends(get_db),
):
    """List all competitors with optional filtering."""
    items, total = CompetitorService.list_all(
        db,
        page=page,
        per_page=per_page,
        sku_id=sku_id,
        marketplace=marketplace,
        is_active=is_active,
        search=search,
    )

    # Use detail response if data is requested (returns CompetitorDetailResponse with data field)
    if include_data:
        return {
            "items": [_competitor_to_detail_response(c).model_dump() for c in items],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": calculate_pages(total, per_page),
        }

    return CompetitorListResponse(
        items=[_competitor_to_response(c) for c in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=calculate_pages(total, per_page),
    )


@router.post("", response_model=CompetitorResponse, status_code=status.HTTP_201_CREATED)
def create_competitor(data: CompetitorCreate, db: Session = Depends(get_db)):
    """Create a new competitor."""
    # Check for duplicate
    existing = (
        db.query(Competitor)
        .filter(
            Competitor.asin == data.asin.upper(),
            Competitor.marketplace == data.marketplace.lower(),
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Competitor with ASIN {data.asin} in marketplace {data.marketplace} already exists",
        )

    competitor = CompetitorService.create(db, data)
    return _competitor_to_response(competitor)


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
def bulk_create_competitors(data: CompetitorBulkCreate, db: Session = Depends(get_db)):
    """Bulk create competitors."""
    created, skipped, errors = CompetitorService.bulk_create(db, data.competitors)
    return {
        "created": created,
        "skipped": skipped,
        "errors": errors,
    }


@router.get("/{competitor_id}", response_model=CompetitorDetailResponse)
def get_competitor(competitor: Competitor = Depends(valid_competitor)):
    """Get competitor details including scraped data."""
    return _competitor_to_detail_response(competitor)


@router.put("/{competitor_id}", response_model=CompetitorResponse)
def update_competitor(
    data: CompetitorUpdate,
    competitor: Competitor = Depends(valid_competitor),
    db: Session = Depends(get_db),
):
    """Update a competitor."""
    updated = CompetitorService.update(db, competitor, data)
    return _competitor_to_response(updated)


@router.delete("/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_competitor(
    competitor: Competitor = Depends(valid_competitor),
    db: Session = Depends(get_db),
):
    """Delete a competitor."""
    CompetitorService.delete(db, competitor)


@router.put("/{competitor_id}/schedule", response_model=CompetitorResponse)
def update_competitor_schedule(
    data: CompetitorScheduleUpdate,
    competitor: Competitor = Depends(valid_competitor),
    db: Session = Depends(get_db),
):
    """Update competitor scrape schedule."""
    updated = CompetitorService.update_schedule(db, competitor, data)
    return _competitor_to_response(updated)


# =============================================================================
# Price History Endpoints
# =============================================================================


@router.get("/{competitor_id}/price-history", response_model=PriceHistoryListResponse)
def get_price_history(
    competitor: Competitor = Depends(valid_competitor),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    """Get price history for a competitor."""
    items, total = CompetitorService.get_price_history(
        db,
        competitor.id,
        page=page,
        per_page=per_page,
        start_date=start_date,
        end_date=end_date,
    )

    return PriceHistoryListResponse(
        items=[PriceHistoryResponse.model_validate(h) for h in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=calculate_pages(total, per_page),
    )


# =============================================================================
# Helper Functions
# =============================================================================


def _competitor_to_response(competitor: Competitor) -> CompetitorResponse:
    """Convert Competitor model to response schema."""
    return CompetitorResponse(
        id=competitor.id,
        sku_id=competitor.sku_id,
        asin=competitor.asin,
        marketplace=competitor.marketplace,
        pack_size=competitor.pack_size,
        display_name=competitor.display_name,
        schedule=competitor.schedule,
        next_scrape_at=competitor.next_scrape_at,
        is_active=competitor.is_active,
        notes=competitor.notes,
        created_at=competitor.created_at,
        updated_at=competitor.updated_at,
        sku_code=competitor.sku.sku_code if competitor.sku else None,
        sku_display_name=competitor.sku.display_name if competitor.sku else None,
    )


def _competitor_to_detail_response(
    competitor: Competitor,
) -> CompetitorDetailResponse:
    """Convert Competitor model to detail response schema."""
    from .schemas import CompetitorDataResponse

    data_response = None
    if competitor.data:
        data_response = CompetitorDataResponse.model_validate(competitor.data)

    return CompetitorDetailResponse(
        id=competitor.id,
        sku_id=competitor.sku_id,
        asin=competitor.asin,
        marketplace=competitor.marketplace,
        pack_size=competitor.pack_size,
        display_name=competitor.display_name,
        schedule=competitor.schedule,
        next_scrape_at=competitor.next_scrape_at,
        is_active=competitor.is_active,
        notes=competitor.notes,
        created_at=competitor.created_at,
        updated_at=competitor.updated_at,
        sku_code=competitor.sku.sku_code if competitor.sku else None,
        sku_display_name=competitor.sku.display_name if competitor.sku else None,
        data=data_response,
    )


def _keyword_to_response(keyword: CompetitorKeyword) -> KeywordResponse:
    """Convert Keyword model to response schema."""
    return KeywordResponse(
        id=keyword.id,
        sku_id=keyword.sku_id,
        keyword=keyword.keyword,
        marketplace=keyword.marketplace,
        notes=keyword.notes,
        created_at=keyword.created_at,
        updated_at=keyword.updated_at,
        sku_code=keyword.sku.sku_code if keyword.sku else None,
        linked_channel_skus_count=len(keyword.channel_sku_links),
        linked_competitors_count=len(keyword.competitor_links),
    )


def _keyword_to_detail_response(keyword: CompetitorKeyword) -> KeywordDetailResponse:
    """Convert Keyword model to detail response schema."""
    return KeywordDetailResponse(
        id=keyword.id,
        sku_id=keyword.sku_id,
        keyword=keyword.keyword,
        marketplace=keyword.marketplace,
        notes=keyword.notes,
        created_at=keyword.created_at,
        updated_at=keyword.updated_at,
        sku_code=keyword.sku.sku_code if keyword.sku else None,
        linked_channel_skus_count=len(keyword.channel_sku_links),
        linked_competitors_count=len(keyword.competitor_links),
        linked_channel_skus=[
            {
                "id": link.channel_sku.id,
                "channel_sku_code": link.channel_sku.channel_sku_code,
                "asin": link.channel_sku.current_asin,
            }
            for link in keyword.channel_sku_links
        ],
        linked_competitors=[
            {
                "id": link.competitor.id,
                "asin": link.competitor.asin,
                "display_name": link.competitor.display_name,
            }
            for link in keyword.competitor_links
        ],
    )


def _scrape_job_to_detail_response(
    job: CompetitorScrapeJob,
) -> ScrapeJobDetailResponse:
    """Convert ScrapeJob model to detail response schema."""
    from .schemas import ScrapeItemResponse

    return ScrapeJobDetailResponse(
        id=job.id,
        job_name=job.job_name,
        status=job.status,
        job_type=job.job_type,
        marketplace=job.marketplace,
        total_competitors=job.total_competitors,
        completed_competitors=job.completed_competitors,
        failed_competitors=job.failed_competitors,
        error_message=job.error_message,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        items=[
            ScrapeItemResponse(
                id=item.id,
                job_id=item.job_id,
                competitor_id=item.competitor_id,
                input_asin=item.input_asin,
                status=item.status,
                error_message=item.error_message,
                apify_run_id=item.apify_run_id,
                started_at=item.started_at,
                completed_at=item.completed_at,
                competitor_display_name=(
                    item.competitor.display_name if item.competitor else None
                ),
            )
            for item in job.items
        ],
    )
