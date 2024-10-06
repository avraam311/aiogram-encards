from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery

from sqlalchemy.ext.asyncio import AsyncSession

from database.requests import (orm_add_user, orm_add_to_words_category,
                               orm_get_words_categories, orm_delete_from_words_category,
                               orm_add_to_words_sub_category, orm_get_words_sub_categories, )
from user_private.menu_processing import get_menu_content
from user_private.keyboards import MenuCB


user_router = Router()


@user_router.message(Command('help'))
async def commamd_help(message: Message):
    await message.answer('Это практическое руководство по использованию бота, но оно пока что не готово, к тому же бот '
                         'интуитивно очень понятен. Приятного изучения!')


@user_router.message(CommandStart())
async def command_start(message: Message, session: AsyncSession) -> None:
    media, reply_markup = await get_menu_content(session, level=0, menu_name="main")
    await message.answer(message.text, reply_markup=ReplyKeyboardRemove())
    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)

    user = message.from_user
    await orm_add_user(
        session,
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=None,
    )
    first_message = await orm_get_words_categories(session, user_id=message.from_user.id)
    if first_message == 0:
        await orm_add_to_words_category(session, user_id=message.from_user.id)
        await message.answer(f"Пользователь {message.from_user.first_name} "
                             f"добавлен в базу данных с каталогом слов \"1\"")


@user_router.callback_query(MenuCB.filter())
async def user_menu(callback: CallbackQuery, callback_data: MenuCB, session: AsyncSession):
    if callback_data.menu_name == "add_to_words_category":

        words_categories_limit = await orm_get_words_categories(session, user_id=callback.from_user.id)
        if words_categories_limit == 26:
            await callback.answer(f'Максимальное количество каталогов слов: 25')

        await orm_add_to_words_category(session, user_id=callback.from_user.id)
        await callback.answer(f'Каталог успешно добавлен')

    elif callback_data.menu_name == "delete_from_words_category":

        await orm_delete_from_words_category(session, user_id=callback.from_user.id,
                                             words_category=callback_data.words_category)
        await callback.answer(f'Каталог успешно удален')

    elif callback_data.menu_name == "add_to_words_sub_category":

        words_sub_categories_limit = await orm_get_words_sub_categories(session, user_id=callback.from_user.id,
                                                                        words_category=callback_data.words_category,)
        if words_sub_categories_limit == 26:
            await callback.answer(f'Максимальное количество пакетов слов: 25')
            return

        await orm_add_to_words_sub_category(session,
                                            user_id=callback.from_user.id,
                                            words_category_id=callback_data.words_category,)
        await callback.answer(f'Пакет успешно добавлен')

    media, reply_markup = await get_menu_content(
        session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category=callback_data.category,
        sub_category=callback_data.sub_category,
        page=callback_data.page,
        user_id=callback.from_user.id,
        words_category=callback_data.words_category,
    )

    await callback.message.edit_media(media=media, reply_markup=reply_markup)
    await callback.answer()
