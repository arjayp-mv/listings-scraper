# =============================================================================
# Amazon Reviews Scraper - Pagination Utilities
# =============================================================================
# Purpose: Shared pagination logic for all list endpoints
# Public API: PaginationParams, PaginatedResponse, paginate_query
# Dependencies: pydantic, fastapi, sqlalchemy
# =============================================================================

from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel
from fastapi import Query
from sqlalchemy.orm import Query as SQLQuery

from .config import settings


T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Pagination parameters for list endpoints.

    Enforces max page size per best practices (50 items max).
    """

    page: int = 1
    page_size: int = settings.default_page_size

    @property
    def offset(self) -> int:
        """Calculate offset for SQL query."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Return capped page size."""
        return min(self.page_size, settings.max_page_size)


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard paginated response wrapper.

    Attributes:
        items: List of items for current page
        total: Total count of all matching items
        page: Current page number
        page_size: Items per page
        total_pages: Total number of pages
        has_next: Whether more pages exist
        has_previous: Whether previous pages exist
    """

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(
        settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description=f"Items per page (max {settings.max_page_size})",
    ),
) -> PaginationParams:
    """
    FastAPI dependency for pagination parameters.

    Example:
        @app.get("/items")
        def list_items(pagination: PaginationParams = Depends(get_pagination_params)):
            ...
    """
    return PaginationParams(page=page, page_size=page_size)


def paginate_query(
    query: SQLQuery,
    pagination: PaginationParams,
) -> tuple[list, int]:
    """
    Apply pagination to SQLAlchemy query.

    Args:
        query: SQLAlchemy query to paginate
        pagination: Pagination parameters

    Returns:
        Tuple of (items list, total count)

    Example:
        query = db.query(Job).filter(Job.status == "completed")
        items, total = paginate_query(query, pagination)
    """
    total = query.count()
    items = query.offset(pagination.offset).limit(pagination.limit).all()
    return items, total


def paginate(query: SQLQuery, page: int = 1, per_page: int = 20) -> tuple[list, int]:
    """
    Apply pagination to SQLAlchemy query using simple page/per_page.

    Args:
        query: SQLAlchemy query to paginate
        page: Page number (1-indexed)
        per_page: Items per page

    Returns:
        Tuple of (items list, total count)

    Example:
        items, total = paginate(db.query(Model), page=1, per_page=20)
    """
    total = query.count()
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()
    return items, total


def calculate_pages(total: int, per_page: int) -> int:
    """
    Calculate total number of pages.

    Args:
        total: Total count of items
        per_page: Items per page

    Returns:
        Total number of pages (minimum 1)
    """
    if total <= 0 or per_page <= 0:
        return 1
    return (total + per_page - 1) // per_page


def create_paginated_response(
    items: List[T],
    total: int,
    pagination: PaginationParams,
) -> dict:
    """
    Create paginated response dictionary.

    Args:
        items: List of items for current page
        total: Total count of all items
        pagination: Pagination parameters used

    Returns:
        Dictionary with pagination metadata
    """
    total_pages = (total + pagination.limit - 1) // pagination.limit if total > 0 else 0

    return {
        "items": items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.limit,
        "total_pages": total_pages,
        "has_next": pagination.page < total_pages,
        "has_previous": pagination.page > 1,
    }
