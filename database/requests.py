from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from database.models import Item, Banner, Category, SubCategory


################### BANNER REQUESTS ####################
async def orm_add_banner_description(session: AsyncSession, data: dict):
    # Добавляем новый или изменяем существующий по именам
    # пунктов меню: main, read!, catalog, sub_catalog, spec_pack, media
    query = select(Banner)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Banner(name=name, description=description) for name, description in data.items()])
    await session.commit()


async def orm_change_banner_image(session: AsyncSession, name: str, image: str):
    query = update(Banner).where(Banner.name == name).values(image=image)
    await session.execute(query)
    await session.commit()


async def orm_get_banner(session: AsyncSession, page: str):
    query = select(Banner).where(Banner.name == page)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_info_pages(session: AsyncSession):
    query = select(Banner)
    result = await session.execute(query)
    return result.scalars().all()
########################################################


################### CATEGORY REQUESTS ####################
async def orm_create_categories(session: AsyncSession, categories: list):
    query = select(Category)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Category(name=name) for name in categories])
    await session.commit()


async def orm_get_categories(session: AsyncSession):
    query = select(Category)
    result = await session.execute(query)
    return result.scalars().all()
########################################################


################### SUB_CATEGORY REQUESTS ####################
async def orm_create_sub_categories(session: AsyncSession, sub_categories: dict):
    query = select(SubCategory)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([SubCategory(name=name, category_id=category_id)
                     for name, category_id in sub_categories.items()])
    await session.commit()


async def orm_get_sub_categories_user(session: AsyncSession, category_id):
    query = select(SubCategory).where(SubCategory.category_id == int(category_id))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_sub_categories_admin(session: AsyncSession):
    query = select(SubCategory)
    result = await session.execute(query)
    return result.scalars().all()

########################################################


################### ITEM REQUESTS ####################
async def orm_add_item(session: AsyncSession, data: dict):
    obj = Item(
        item_media=data["item_media"],
        media_text=data["media_text"],
        sub_category_id=int(data["sub_category_id"]),
    )
    session.add(obj)
    await session.commit()


async def orm_get_items(session: AsyncSession, sub_category_id):
    query = select(Item).where(Item.sub_category_id == int(sub_category_id))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_item(session: AsyncSession, item_id: int):
    query = select(Item).where(Item.id == item_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_item(session: AsyncSession, item_id: int, data: dict):
    query = update(Item).where(Item.id == item_id).values(
        item_media=data["item_media"],
        media_text=data["media_text"],
    )
    await session.execute(query)
    await session.commit()


async def orm_delete_item(session: AsyncSession, item_id: int):
    query = delete(Item).where(Item.id == item_id)
    await session.execute(query)
    await session.commit()
########################################################
