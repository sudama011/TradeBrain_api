"""
Base repository pattern implementation for data access layer.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Literal, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import handle_exceptions
from app.core.logger import get_logger
from app.db.query_builder import AsyncQueryBuilder
from app.schemas import PaginatedResponse, PaginationParams

T = TypeVar("T")
RelationshipStrategy = Literal["selectin", "joined", "subquery", "noload"]
RelationshipLoading = Dict[str, RelationshipStrategy]


class IRepository(ABC, Generic[T]):
    """Async repository interface for standard CRUD operations."""

    @abstractmethod
    async def get_by_field(
        self,
        field_name: str,
        value: Any,
        session: AsyncSession,
        relationships: Optional[List[str]] = None,
    ) -> Optional[T]:
        pass

    @abstractmethod
    async def get_by_id(
        self,
        entity_id: UUID,
        session: AsyncSession,
        relationships: Optional[List[str]] = None,
    ) -> Optional[T]:
        pass

    @abstractmethod
    async def get_paginated(
        self,
        session: AsyncSession,
        pagination: PaginationParams,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[tuple]] = None,
        relationships: Optional[RelationshipLoading] = None,
    ) -> PaginatedResponse[T]:
        pass

    @abstractmethod
    async def create(self, entity: T, session: AsyncSession) -> T:
        pass

    @abstractmethod
    async def update(self, entity: T, session: AsyncSession) -> T:
        pass

    @abstractmethod
    async def delete(self, entity_id: UUID, session: AsyncSession) -> bool:
        pass

    @abstractmethod
    async def exists(self, entity_id: UUID, session: AsyncSession) -> bool:
        pass

    @abstractmethod
    async def count(self, session: AsyncSession, filters: Optional[Dict[str, Any]] = None) -> int:
        pass

    @abstractmethod
    async def bulk_create(self, entities: List[T], session: AsyncSession) -> List[T]:
        pass

    @abstractmethod
    async def bulk_update(self, entities: List[T], session: AsyncSession) -> List[T]:
        pass

    @abstractmethod
    async def bulk_delete(self, entities: List[T], session: AsyncSession) -> None:
        pass


class BaseRepository(IRepository[T], Generic[T]):
    """
    Base repository implementation using AsyncQueryBuilder for common async CRUD operations.
    """

    def __init__(self, model_class: Type[T]):
        self.model_class = model_class
        self.logger = get_logger(f"repository.{model_class.__name__.lower()}")

    def _get_query_builder(self, session: AsyncSession) -> AsyncQueryBuilder:
        """Helper method to get a new instance of AsyncQueryBuilder."""
        return AsyncQueryBuilder(self.model_class, session)

    @handle_exceptions(operation_type="database")
    async def get_by_field(
        self,
        field_name: str,
        value: Any,
        session: AsyncSession,
        relationships: Optional[List[str]] = None,
    ) -> Optional[T]:
        builder = self._get_query_builder(session).filter_by_fields({field_name: value})
        if relationships:
            builder = builder.with_relationships(*relationships)

        return await builder.first()

    @handle_exceptions(operation_type="database")
    async def get_by_id(
        self,
        entity_id: UUID,
        session: AsyncSession,
        relationships: Optional[List[str]] = None,
    ) -> Optional[T]:
        builder = self._get_query_builder(session).filter_by_pk(entity_id)
        if relationships:
            builder = builder.with_relationships(*relationships)

        return await builder.first()

    @handle_exceptions(operation_type="database")
    async def get_paginated(
        self,
        session: AsyncSession,
        pagination: PaginationParams,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[tuple]] = None,
        relationships: Optional[RelationshipLoading] = None,
    ) -> PaginatedResponse[T]:
        builder = self._get_query_builder(session)

        if filters:
            builder = builder.filter_by_fields(filters)

        if order_by:
            builder = builder.order_by_fields(order_by)

        if relationships:
            for relationship_name, strategy in relationships.items():
                if strategy == "noload":
                    builder = builder.without_relationships(relationship_name)
                else:
                    builder = builder.with_relationships(relationship_name, strategy=strategy)

        return await builder.paginate(pagination)

    @handle_exceptions(operation_type="database")
    async def create(self, entity: T, session: AsyncSession) -> T:
        session.add(entity)
        await session.commit()
        await session.refresh(entity)
        self.logger.info(f"Created {self.model_class.__name__} with ID: {entity.id}")  # type: ignore
        return entity

    @handle_exceptions(operation_type="database")
    async def update(self, entity: T, session: AsyncSession) -> T:
        session.add(entity)
        await session.commit()
        await session.refresh(entity)
        self.logger.info(f"Updated {self.model_class.__name__} with ID: {entity.id}")  # type: ignore
        return entity

    @handle_exceptions(operation_type="database")
    async def delete(self, entity_id: UUID, session: AsyncSession) -> bool:
        entity = await self.get_by_id(entity_id, session)
        if not entity:
            return False

        await session.delete(entity)
        await session.commit()
        self.logger.info(f"Deleted {self.model_class.__name__} with ID: {entity_id}")
        return True

    @handle_exceptions(operation_type="database")
    async def exists(self, entity_id: UUID, session: AsyncSession) -> bool:
        builder = self._get_query_builder(session).filter_by_pk(entity_id)
        count_result = await builder.count()
        return count_result > 0

    @handle_exceptions(operation_type="database")
    async def count(self, session: AsyncSession, filters: Optional[Dict[str, Any]] = None) -> int:
        builder = self._get_query_builder(session)
        if filters:
            builder = builder.filter_by_fields(filters)
        return await builder.count()

    @handle_exceptions(operation_type="database")
    async def bulk_create(self, entities: List[T], session: AsyncSession) -> List[T]:
        session.add_all(entities)
        await session.commit()

        for entity in entities:
            await session.refresh(entity)

        self.logger.info(f"Bulk created {len(entities)} {self.model_class.__name__} entities")
        return entities

    @handle_exceptions(operation_type="database")
    async def bulk_update(self, entities: List[T], session: AsyncSession) -> List[T]:
        for entity in entities:
            await session.merge(entity)
        await session.commit()

        for entity in entities:
            await session.refresh(entity)

        self.logger.info(f"Bulk updated {len(entities)} {self.model_class.__name__} entities")
        return entities

    @handle_exceptions(operation_type="database")
    async def bulk_delete(self, entities: List[T], session: AsyncSession) -> None:
        for entity in entities:
            await session.delete(entity)
        await session.commit()

        self.logger.info(f"Bulk deleted {len(entities)} {self.model_class.__name__} entities")
        return None
