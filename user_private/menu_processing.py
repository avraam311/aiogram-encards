from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.types import InputMediaDocument, InputMediaPhoto

from database.requests import orm_get_banner, orm_get_categories, orm_get_items
from user_private.keyboards import get_user_main_btns, get_user_catalog_btns, get_items_btns
from common.paginator import Paginator


def pages(paginator: Paginator):
    btns = dict()
    if paginator.has_previous():
        btns["◀ Пред."] = "previous"

    if paginator.has_next():
        btns["След. ▶"] = "next"

    return btns


async def main_menu(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    kbds = get_user_main_btns(level=level)

    return image, kbds


async def f_catalog(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    categories = await orm_get_categories(session)
    kbds = get_user_catalog_btns(level=level, categories=categories)

    return image, kbds


async def f_items(session, level, category, page):
    items = await orm_get_items(session, category_id=category)
    paginator = Paginator(items, page=page)
    item = paginator.get_page()[0]

    media = InputMediaDocument(
        media=item.item_media,
        caption=f"<strong>{item.media_text}</strong>\n"
                f"<strong>{paginator.page} из {paginator.pages}</strong>",
    )

    pagination_btns = pages(paginator)

    kbds = get_items_btns(
        level=level,
        category=category,
        page=page,
        pagination_btns=pagination_btns,
    )

    return media, kbds


async def get_menu_content(
    session: AsyncSession,
    level: int,
    menu_name: str,
    category: int | None = None,
    page: int | None = None,
):
    if level == 0:
        return await main_menu(session, level, menu_name)
    elif level == 1:
        return await f_catalog(session, level, menu_name)
    elif level == 2:
        return await f_items(session, level, category, page)
