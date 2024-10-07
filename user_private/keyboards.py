from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData


class MenuCB(CallbackData, prefix="menu"):
    level: int
    menu_name: str
    category: int | None = None
    sub_category: int | None = None
    page: int = 1
    item_id: int | None = None
    user_id: int | None = None


def get_user_main_btns(*, level: int, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    btns = {
        "Изучать": 'catalog',
        "Прочитать!": 'read!',
        "Спец. пакет": 'spec_pack',
    }
    for text, menu_name in btns.items():
        if menu_name in ['catalog']:
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCB(level=level+1, menu_name=menu_name).pack()))
        else:
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCB(level=level, menu_name=menu_name).pack()))

    return keyboard.adjust(*sizes).as_markup()


def get_user_catalog_btns(*, level: int, categories: list, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for i in categories:
        keyboard.add(InlineKeyboardButton(text=i.name,
                                          callback_data=MenuCB(level=level + 1,
                                                               menu_name='sub_catalog',
                                                               category=i.id).pack()))

    keyboard.add(InlineKeyboardButton(text="Назад",
                                      callback_data=MenuCB(level=level - 1, menu_name='main').pack()))

    return keyboard.adjust(*sizes).as_markup()


def get_user_sub_catalog_btns(*, level: int, category: int, sub_categories: list, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for i in sub_categories:
        keyboard.add(InlineKeyboardButton(text=i.name,
                                          callback_data=MenuCB(level=level + 1,
                                                               menu_name=i.name,
                                                               category=category,
                                                               sub_category=i.id).pack()))

    keyboard.add(InlineKeyboardButton(text="Назад",
                                      callback_data=MenuCB(level=level - 1, menu_name='catalog').pack()))
    keyboard.add(InlineKeyboardButton(text="На главную",
                                      callback_data=MenuCB(level=0, menu_name='main').pack()))

    return keyboard.adjust(*sizes).as_markup()


def get_items_btns(
        *,
        level: int,
        category: int | None,
        sub_category: int | None,
        page: int | None,
        pagination_btns: dict | None,
        sizes: tuple[int] = (2,)
):
    keyboard = InlineKeyboardBuilder()

    keyboard.adjust(*sizes)

    keyboard.add(InlineKeyboardButton(text="Назад",
                                      callback_data=MenuCB(level=level - 1,
                                                           menu_name='sub_catalog',
                                                           category=category).pack()))
    keyboard.add(InlineKeyboardButton(text="На главную",
                                      callback_data=MenuCB(level=0,
                                                           menu_name='main').pack()))

    if page:
        row = []
        for text, menu_name in pagination_btns.items():
            if menu_name == "next":
                row.append(InlineKeyboardButton(text=text,
                                                callback_data=MenuCB(
                                                    level=level,
                                                    menu_name=menu_name,
                                                    category=category,
                                                    sub_category=sub_category,
                                                    page=page + 1).pack()))

            elif menu_name == "previous":
                row.append(InlineKeyboardButton(text=text,
                                                callback_data=MenuCB(
                                                    level=level,
                                                    menu_name=menu_name,
                                                    category=category,
                                                    sub_category=sub_category,
                                                    page=page - 1).pack()))

        keyboard.row(*row)

    return keyboard.as_markup()
