from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import ColumnElement, select
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Generic async CRUD. Subclass it to add model-specific queries."""

    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: int) -> ModelType | None:
        return await db.get(self.model, id)

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        filters: Sequence[ColumnElement[bool]] = (),
        order_by: Sequence[Any] = (),
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[ModelType]:
        stmt = select(self.model).where(*filters)
        stmt = stmt.order_by(*(order_by or sa_inspect(self.model).primary_key))
        result = await db.scalars(stmt.offset(offset).limit(limit))
        return result.all()

    async def create(
        self, db: AsyncSession, obj_in: CreateSchemaType, **extra: Any
    ) -> ModelType:
        """`extra` carries server-controlled fields such as created_by."""
        obj = self.model(**obj_in.model_dump(), **extra)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def update(
        self, db: AsyncSession, db_obj: ModelType, obj_in: UpdateSchemaType
    ) -> ModelType:
        columns = sa_inspect(self.model).columns
        for field, value in obj_in.model_dump(exclude_unset=True).items():
            # Sending null for a required column means "leave unchanged".
            if value is None and not columns[field].nullable:
                continue
            setattr(db_obj, field, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, db_obj: ModelType) -> None:
        await db.delete(db_obj)
        await db.commit()
