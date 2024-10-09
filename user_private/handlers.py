from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery

from sqlalchemy.ext.asyncio import AsyncSession

from database.requests import orm_add_user, orm_status_user_spec_pack
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
    first_message = await orm_add_user(
                        session,
                        user_id=user.id,
                        first_name=user.first_name,
                        last_name=user.last_name,
    )
    if first_message:
        await message.answer(f"Пользователь {message.from_user.first_name} добавлен в базу данных")


@user_router.callback_query(MenuCB.filter())
async def user_menu(callback: CallbackQuery, callback_data: MenuCB, session: AsyncSession):
    if callback_data.category == 5:
        spec_pack_check = await orm_status_user_spec_pack(session, user_id=callback.from_user.id)
        if not spec_pack_check:
            await callback.answer(text='Купите спец. пакет, чтобы изучать английский еще эффективнее!'
                                       'Отправьте команду \"Спец. пакет\" из меню или напишите вручную'
                                       '\"spec_pack\"',
                                  show_alert=True,)
            return

    media, reply_markup = await get_menu_content(
        session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category=callback_data.category,
        sub_category=callback_data.sub_category,
        page=callback_data.page,
    )

    await callback.message.edit_media(media=media, reply_markup=reply_markup)
    await callback.answer()
