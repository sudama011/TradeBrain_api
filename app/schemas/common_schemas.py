"""
Common models for pagination, search, and API responses.

Provides reusable Pydantic models for consistent data structures
across the application.
"""

from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

# Define a TypeVar for generics
T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for database queries."""

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.size


class PaginationMeta(BaseModel):
    """Pagination metadata for responses."""

    page: int = Field(description="Current page number")
    size: int = Field(description="Items per page")
    total: int = Field(description="Total number of items")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response with metadata."""

    items: List[T] = Field(description="List of items for current page")
    meta: PaginationMeta = Field(description="Pagination metadata")


class SortOrderEnum(str, Enum):
    """Enum for sort order."""

    asc = "asc"
    desc = "desc"


class SearchParams(BaseModel):
    """Search and filtering parameters."""

    query: Optional[str] = Field(default=None, description="Search query string")
    fields: List[str] = Field(default=[], description="Fields to search in")
    filters: Dict[str, Any] = Field(default={}, description="Additional filters")
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: SortOrderEnum = Field(default=SortOrderEnum.asc, description="Sort order (asc/desc)")


def get_pagination_meta(total: int, page: int, size: int) -> PaginationMeta:
    if size <= 0:
        pages = 0
    else:
        pages = (total + size - 1) // size

    return PaginationMeta(
        page=page,
        size=size,
        total=total,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1,
    )


def get_paginated_response(items: List[T], total: int, page: int, size: int) -> PaginatedResponse[T]:
    """
    Generate a complete paginated response object.
    """
    meta = get_pagination_meta(total, page, size)
    return PaginatedResponse(items=items, meta=meta)
