import logging
from logging import config as logging_config
from typing import Any, Generic, Optional, Type, TypeVar
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from shortuuid import ShortUUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import LOGGING
from db.short_links_db_base import Base

logging_config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


class Repository:

    def get(self, *args, **kwargs):
        raise NotImplementedError

    def update_multi(self, *args, **kwargs):
        raise NotImplementedError

    def create(self, *args, **kwargs):
        raise NotImplementedError

    def update(self, *args, **kwargs):
        raise NotImplementedError

    def delete(self, *args, **kwargs):
        raise NotImplementedError


ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class RepositoryDB(Repository, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):

    def __init__(self, model: Type[ModelType]):
        self._model = model

    @staticmethod
    def create_short_url(url_len: int) -> str:
        return ShortUUID().random(length=url_len)

    async def get(self, db: AsyncSession, id_: Any) -> Optional[ModelType]:
        statement = select(self._model).where(self._model.id_ == id_)
        results = await db.execute(statement=statement)
        return results.scalar_one_or_none()

    async def get_for_shorten_url(self, db: AsyncSession, shorten_url_id: Any) -> Optional[ModelType]:
        statement = select(self._model).where(self._model.link_id == shorten_url_id)
        results = await db.execute(statement=statement)
        return results.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self._model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
            self,
            db: AsyncSession,
            *,
            db_obj: ModelType,
            obj_in: UpdateSchemaType,
    ) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db.add(db_obj)
        await db.execute(update(self._model).where(self._model.id == db_obj.id).values(obj_in_data))
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, db_obj: ModelType,) -> ModelType:
        db.add(db_obj)
        await db.execute(update(self._model).where(self._model.id == db_obj.id).values({"is_active": False}))
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update_multi(self, db: AsyncSession, *, objects_in: CreateSchemaType):
        db_objects = [self._model(**jsonable_encoder(obj_in)) for obj_in in objects_in.__root__]
        db.add_all(db_objects)
        await db.commit()
        db.expire_all()
        db_objects = await db.execute(
            select(self._model).where(self._model.link_id.in_(i.link_id for i in objects_in.__root__))
        )
        return db_objects.scalars().all()

    async def get_detail_history(self, db: AsyncSession, *, link_id: UUID, limit: int, offset):
        db_objects = await db.execute(
            select(self._model).where(self._model.short_link_id == link_id).offset(offset).limit(limit)
        )
        return db_objects.scalars().all()

    @staticmethod
    async def ping_db(db: AsyncSession) -> bool:
        try:
            await db.connection()
            return True
        except ConnectionRefusedError as err:
            logger.error("ping_db and with err: %s", str(err))
            return False
