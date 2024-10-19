from sqlalchemy.ext.asyncio import AsyncSession

from aiogram.types import InputMediaPhoto, InputMediaVideo

from database.requests import (orm_get_banner, orm_get_categories,
                               orm_get_sub_categories_user, orm_get_items,)
from user_private.keyboards import (get_user_main_btns, get_user_catalog_btns,
                                    get_user_sub_catalog_btns, get_items_btns,)
from common.paginator import Paginator
from cache import Cache
import config


config = config.Config()

redis_db = Cache(username=config.redis_username, password=config.redis_password,
                 host=config.redis_host, port=config.redis_port, db=config.redis_db)


def pages(paginator: Paginator):
    btns = dict()
    if paginator.has_previous():
        btns["◀ Пред."] = "previous"

    if paginator.has_next():
        btns["След. ▶"] = "next"

    if paginator.has_previous_10():
        btns["⏪ -10"] = "previous_10"

    if paginator.has_next_10:
        btns["+10 ⏩"] = "next_10"

    return btns


async def main_menu(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    kbds = get_user_main_btns(level=level)

    return image, kbds


async def f_catalog(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    categories = redis_db.get_categories_list()
    if categories is None:
        categories = await orm_get_categories(session)
        redis_db.set_categories_list(categories)

    kbds = get_user_catalog_btns(level=level, categories=categories)

    return image, kbds


async def f_sub_catalog(session, level, category, menu_name):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    sub_categories = redis_db.get_sub_categories_list_user(category)

    if sub_categories is None:
        sub_categories = await orm_get_sub_categories_user(session, category)
        redis_db.set_sub_categories_list_user(sub_categories, category)

    kbds = get_user_sub_catalog_btns(level=level, category=category, sub_categories=sub_categories)

    return image, kbds


async def f_items(session, level, category, sub_category, page):
    items = redis_db.get_items_list(sub_category)
    if items is None:
        items = await orm_get_items(session, int(sub_category))
        redis_db.set_items_list(items, sub_category)

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
            items_len=None
        )

    else:
        items_len = len(items)

        if int(sub_category) in [2, 7]:
            input_media_photo_or_video = InputMediaVideo
        else:
            input_media_photo_or_video = InputMediaPhoto

        paginator = Paginator(items, page=page)
        item = paginator.get_page()[0]

        media = input_media_photo_or_video(
            media=item[1],
            caption=f"<strong>{item[2]}</strong>\n\n"
                    f"<strong>{paginator.page} из {paginator.pages}</strong>",
            )

        pagination_btns = pages(paginator)

        kbds = get_items_btns(
            level=level,
            category=category,
            sub_category=sub_category,
            page=page,
            pagination_btns=pagination_btns,
            sizes=(2, 2, 2),
            items_len=items_len,
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
