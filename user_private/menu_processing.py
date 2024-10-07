from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.types import InputMediaPhoto, InputMediaVideo

from database.requests import (orm_get_banner, orm_get_categories,
                               orm_get_sub_categories_user, orm_get_items,)

from user_private.keyboards import (get_user_main_btns, get_user_catalog_btns,
                                    get_user_sub_catalog_btns, get_items_btns,)
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


async def f_sub_catalog(session, level, category, menu_name):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    sub_categories = await orm_get_sub_categories_user(session, category_id=category)
    kbds = get_user_sub_catalog_btns(level=level, category=category, sub_categories=sub_categories)

    return image, kbds


async def f_items(session, level, category, sub_category, page):
    items = await orm_get_items(session, sub_category_id=sub_category)

    if not items:
        banner = await orm_get_banner(session, "media")
        media = InputMediaPhoto(
            media=banner.image, caption=banner.description
        )

        kbds = get_items_btns(
            level=level,
            category=category,
            sub_category=None,
            page=None,
            pagination_btns=None,
        )

    else:
        if int(sub_category) in [2, 7]:
            input_media_photo_or_video = InputMediaVideo
        else:
            input_media_photo_or_video = InputMediaPhoto

        paginator = Paginator(items, page=page)
        item = paginator.get_page()[0]

        media = input_media_photo_or_video(
            media=item.item_media,
            caption=f"<strong>{item.media_text}</strong>\n\n"
                    f"<strong>{paginator.page} из {paginator.pages}</strong>",
            )

        pagination_btns = pages(paginator)

        kbds = get_items_btns(
            level=level,
            category=category,
            sub_category=sub_category,
            page=page,
            pagination_btns=pagination_btns,
        )

    return media, kbds


async def get_menu_content(
    session: AsyncSession,
    level: int,
    menu_name: str,
    category: int | None = None,
    sub_category: int | None = None,
    page: int | None = None,
):
    if level == 0:
        return await main_menu(session, level, menu_name)
    elif level == 1:
        return await f_catalog(session, level, menu_name)
    elif level == 2:
        return await f_sub_catalog(session, level, category, menu_name)
    elif level == 3:
        return await f_items(session, level, category, sub_category, page)
