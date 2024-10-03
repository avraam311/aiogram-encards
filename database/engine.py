import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models import Base
from common.texts_for_db import description_for_info_pages, categories, sub_categories
from database.requests import (orm_add_banner_description, orm_create_categories,
                               orm_create_sub_categories,)


engine = create_async_engine(url=os.getenv('PSQL_URL'), echo=True)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        await orm_create_categories(session, categories)
        await orm_create_sub_categories(session, sub_categories)
        await orm_add_banner_description(session, description_for_info_pages)


async def drop_all():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
