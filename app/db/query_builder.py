"""
Query builder utilities for reducing repository code duplication.
"""

from typing import Any, Dict, Generic, List, Optional, Tuple, Type, TypeVar, Union, cast
from uuid import UUID

from sqlalchemy import and_, asc, desc, distinct, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, load_only, noload, selectinload, subqueryload
from sqlalchemy.sql.selectable import Select

from app.core.exceptions import handle_exceptions
from app.core.logging import get_logger
from app.schemas import (
    PaginatedResponse,
    PaginationParams,
    SearchParams,
    SortOrderEnum,
    get_paginated_response,
)

logger = get_logger(__name__)

# TypeVar for any SQLAlchemy mapped class
T = TypeVar("T")


class AsyncQueryBuilder(Generic[T]):
    """Generic query builder for common asynchronous database operations."""

    def __init__(self, model_class: Type[T], session: AsyncSession, pk_field: str = "id"):
        self.model_class = model_class
        self.session = session
        self.pk_field = pk_field
        self._filters: List[Any] = []
        self._options: List[Any] = []
        self._order_by: List[Any] = []
        self._joins: List[Dict[str, Any]] = []
        self._distinct: bool = False
        self._group_by: List[Any] = []
        self._having: List[Any] = []

    def select_columns(self, *columns: str) -> "AsyncQueryBuilder":
        """Load only specific columns for a performance boost using load_only."""
        fields = [getattr(self.model_class, col) for col in columns if hasattr(self.model_class, col)]
        self._options.append(load_only(*fields))
        return self

    def filter_by_pk(self, entity_id: Union[UUID, str, int]) -> "AsyncQueryBuilder":
        """Filter by the configurable primary key field."""
        if hasattr(self.model_class, self.pk_field):
            pk_column = getattr(self.model_class, self.pk_field)
            self._filters.append(pk_column == entity_id)
        return self

    def filter_by_fields(self, filters: Dict[str, Any]) -> "AsyncQueryBuilder":
        """Add multiple field filters to query."""
        for field_name, value in filters.items():
            if value is not None and hasattr(self.model_class, field_name):
                field = getattr(self.model_class, field_name)
                if isinstance(value, list):
                    self._filters.append(field.in_(value))
                else:
                    self._filters.append(field == value)
        return self

    def filter_active_only(self) -> "AsyncQueryBuilder":
        """Filter for records with is_active=True."""
        if hasattr(self.model_class, "is_active"):
            self._filters.append(getattr(self.model_class, "is_active"))
        return self

    def advanced_filter(self, *filters) -> "AsyncQueryBuilder":
        """Add custom filter clauses directly."""
        self._filters.extend(filters)
        return self

    def search(self, params: SearchParams) -> "AsyncQueryBuilder":
        """Build a search query with filters and sorting."""
        if "query" in params and "fields" in params:
            search_conditions = [
                getattr(self.model_class, field).ilike(f"%{params['query']}%")
                for field in params["fields"]
                if hasattr(self.model_class, field)
            ]
            if search_conditions:
                self._filters.append(or_(*search_conditions))

        if "filters" in params:
            self.filter_by_fields(params["filters"])

        if "sort_by" in params and hasattr(self.model_class, params["sort_by"]):
            sort_order = params["sort_order"]
            if sort_order == SortOrderEnum.desc:
                self._order_by.append(desc(getattr(self.model_class, params["sort_by"])))
            else:
                self._order_by.append(asc(getattr(self.model_class, params["sort_by"])))
        elif hasattr(self.model_class, self.pk_field):
            self._order_by.append(asc(getattr(self.model_class, self.pk_field)))
        return self

    def with_relationships(self, *relationships: str, strategy: str = "selectin") -> "AsyncQueryBuilder":
        """
        Add relationship loading options.
        Strategy can be 'selectin', 'joined', or 'subquery'.
        """
        for relationship_name in relationships:
            if not hasattr(self.model_class, relationship_name):
                continue
            relationship = getattr(self.model_class, relationship_name)
            if strategy == "joined":
                self._options.append(joinedload(relationship))
            elif strategy == "subquery":
                self._options.append(subqueryload(relationship))
            else:  # Default to selectinload
                self._options.append(selectinload(relationship))
        return self

    def without_relationships(self, *relationships: str) -> "AsyncQueryBuilder":
        """Exclude relationship loading options."""
        for relationship_name in relationships:
            if not hasattr(self.model_class, relationship_name):
                continue
            relationship = getattr(self.model_class, relationship_name)
            self._options.append(noload(relationship))
        return self

    def join(self, model: Type[T], on_clause=None, isouter: bool = False) -> "AsyncQueryBuilder":
        """Add a join clause to the query."""
        self._joins.append({"model": model, "on": on_clause, "isouter": isouter})
        return self

    def distinct(self) -> "AsyncQueryBuilder":
        """Apply a DISTINCT clause to the query."""
        self._distinct = True
        return self

    def group_by(self, *fields: str) -> "AsyncQueryBuilder":
        """Add a GROUP BY clause."""
        self._group_by.extend(
            [getattr(self.model_class, field) for field in fields if hasattr(self.model_class, field)]
        )
        return self

    def having(self, *clauses: Any) -> "AsyncQueryBuilder":
        """Add a HAVING clause."""
        self._having.extend(clauses)
        return self

    def order_by_fields(self, sort_fields: List[Tuple[str, str]]) -> "AsyncQueryBuilder":
        """Order the results by multiple fields."""
        for field_name, order in sort_fields:
            if hasattr(self.model_class, field_name):
                field = getattr(self.model_class, field_name)
                order_clause: Any = desc(field) if order == "desc" else asc(field)
                self._order_by.append(order_clause)
        return self

    def _build(self) -> Select:
        """Internal method to build the final query statement without execution."""
        query = select(self.model_class)

        if self._distinct:
            query = query.distinct()

        for join_info in self._joins:
            query = query.join(
                join_info["model"],
                onclause=join_info["on"],
                isouter=join_info["isouter"],
            )

        if self._filters:
            query = query.where(and_(*self._filters))

        if self._group_by:
            query = query.group_by(*self._group_by)

        if self._having:
            query = query.having(and_(*self._having))

        if self._options:
            query = query.options(*self._options)

        if self._order_by:
            query = query.order_by(*self._order_by)
        else:
            if hasattr(self.model_class, self.pk_field):
                query = query.order_by(asc(getattr(self.model_class, self.pk_field)))

        return cast(Select, query)

    @handle_exceptions(operation_type="database")
    async def first(self) -> Optional[T]:
        """Execute query and return the first result."""
        query = self._build()
        result = await self.session.execute(query)
        return result.scalars().first()

    @handle_exceptions(operation_type="database")
    async def all(self) -> List[T]:
        """Execute query and return all results."""
        query = self._build()
        result = await self.session.execute(query)
        return list(result.scalars().all())

    @handle_exceptions(operation_type="database")
    async def count(self) -> int:
        """Execute query and return the total count."""
        pk_column = getattr(self.model_class, self.pk_field)
        count_query = select(func.count(distinct(pk_column) if self._distinct else pk_column)).select_from(
            self.model_class
        )

        for join_info in self._joins:
            count_query = count_query.join(
                join_info["model"],
                onclause=join_info["on"],
                isouter=join_info["isouter"],
            )

        if self._filters:
            count_query = count_query.where(and_(*self._filters))

        count_result = await self.session.execute(count_query)
        return count_result.scalar_one()

    @handle_exceptions(operation_type="database")
    async def paginate(self, pagination: PaginationParams) -> PaginatedResponse[T]:
        """Apply offset-based pagination to the built query."""
        total = await self.count()
        if total > 0:
            query: Select = self._build().offset(pagination.offset).limit(pagination.size)
            paginated_result = await self.session.execute(query)

            logger.info(
                "Paginated query executed successfully",
                total=total,
                page=pagination.page,
                size=pagination.size,
            )

            items = list(paginated_result.scalars().all())
        else:
            items = []
        return get_paginated_response(items=items, total=total, page=pagination.page, size=pagination.size)
