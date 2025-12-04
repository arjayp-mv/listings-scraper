# =============================================================================
# Competitors Domain - FastAPI Dependencies
# =============================================================================
# Purpose: Dependency injection for competitor routes
# Public API: valid_competitor, valid_keyword, valid_scrape_job
# Dependencies: fastapi, sqlalchemy
# =============================================================================

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from .models import Competitor, CompetitorKeyword, CompetitorScrapeJob
from .service import CompetitorService


def valid_competitor(
    competitor_id: int, db: Session = Depends(get_db)
) -> Competitor:
    """Validate that competitor exists and return it."""
    competitor = CompetitorService.get_by_id(db, competitor_id)
    if not competitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Competitor with ID {competitor_id} not found",
        )
    return competitor


def valid_keyword(
    keyword_id: int, db: Session = Depends(get_db)
) -> CompetitorKeyword:
    """Validate that keyword exists and return it."""
    keyword = CompetitorService.get_keyword_by_id(db, keyword_id)
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Keyword with ID {keyword_id} not found",
        )
    return keyword


def valid_scrape_job(
    job_id: int, db: Session = Depends(get_db)
) -> CompetitorScrapeJob:
    """Validate that scrape job exists and return it."""
    job = CompetitorService.get_scrape_job_by_id(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scrape job with ID {job_id} not found",
        )
    return job
