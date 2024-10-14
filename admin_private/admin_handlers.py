import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command, or_f, StateFilter
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery

from sqlalchemy.ext.asyncio import AsyncSession

from admin_private import admin_keyboards as kb
from common.filters import IsAdmin
from database.requests import (orm_add_item, orm_get_item, orm_get_items, orm_delete_item,
                               orm_update_item, orm_get_info_pages, orm_change_banner_image,
                               orm_get_sub_categories_admin)
from common.get_keyboard_func import get_inline_keyboard

from cache import Cache

redis_db = Cache(host=os.getenv('REDIS_HOST'), port=int(os.getenv('REDIS_PORT')), db=0)


admin_router = Router()
admin_router.message.filter(IsAdmin())


@admin_router.message(Command("admin"))
async def admin_features(message: Message, state: FSMContext):
    await message.answer("Что хотите сделать❓", reply_markup=kb.admin_main)
    await state.clear()


@admin_router.message(F.text == 'Просмотреть🕶')
async def admin_features(message: Message, session: AsyncSession):
    sub_categories = await redis_db.get_sub_categories_dict_admin()

    if sub_categories is None:
        sub_categories = await orm_get_sub_categories_admin(session)
        await redis_db.set_sub_categories_list_admin(sub_categories)

    btns = {sub_category.name: f'sub_category_{sub_category.id}' for sub_category in sub_categories}
    await message.answer("Выберите подкатегорию:", reply_markup=get_inline_keyboard(btns=btns))


@admin_router.message(F.text == "Ничего🌊")
async def nth(message: Message, state: FSMContext) -> None:
    await message.answer(
        message.text,
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(None)


@admin_router.callback_query(F.data.startswith('sub_category_'))
async def starring_at_item(callback: CallbackQuery, session: AsyncSession):
    if int(callback.data.split('_')[-1]) in [2, 7]:
        answer_photo_or_video = callback.message.answer_video
    else:
        answer_photo_or_video = callback.message.answer_photo

    sub_category_id = callback.data.split('_')[-1]

    items = await redis_db.get_items_list(sub_category_id)
    if items is None:
        items = await orm_get_items(session, int(sub_category_id))
        await redis_db.set_items_list(sub_category_id, items)

    for item in items:
        item_id = item[0]
        await answer_photo_or_video(
            item[1],
            caption=f"<strong>{item[2]}</strong>\n",
            reply_markup=get_inline_keyboard(
                btns={
                    "Удалить🧺": f"delete_{item_id}",
                    "Изменить✅": f"change_{item_id}",
                },
                sizes=(2,)
            ),
        )
    await callback.message.answer("ОК, вот список⏫")
    await callback.answer()


@admin_router.callback_query(F.data.startswith("delete_"))
async def delete_item_callback(callback: CallbackQuery, session: AsyncSession):
    item_id = callback.data.split("_")[-1]
    await orm_delete_item(session, int(item_id))

    await callback.message.answer("Удаление прошло успешно✅")
    await callback.message.delete()


################# Микро FSM для загрузки/изменения баннеров ############################

class AddItemBanner(StatesGroup):
    image = State()


# Отправляем перечень информационных страниц бота и становимся в состояние отправки photo
@admin_router.message(StateFilter(None), F.text == 'Добавить/Изменить баннер🔂')
async def add_image2(message: Message, state: FSMContext, session: AsyncSession):
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    await message.answer(f"Отправьте изображение баннера📷\n\nВ описании укажите для какой страницы:\
                         \n\n{', '.join(pages_names)}⭕",
                         reply_markup=kb.admin_cancel)
    await state.set_state(AddItemBanner.image)


@admin_router.message(AddItemBanner.image, F.text == 'Отмена❌')
async def add_banner(message: Message, state: FSMContext):
    await message.answer(message.text, reply_markup=kb.admin_main)
    await state.clear()


# Добавляем/изменяем изображение в таблице (там уже есть записанные страницы по именам:
# main, read!, catalog, sub_catalog, spec_pack, media
@admin_router.message(AddItemBanner.image, F.photo)
async def add_banner(message: Message, state: FSMContext, session: AsyncSession):
    image_id = message.photo[-1].file_id
    for_page = message.caption.strip()
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    if for_page not in pages_names:
        await message.answer(f"Введите нормальное название страницы, например:\
                         \n\n{', '.join(pages_names)}")
        return
    await orm_change_banner_image(session, for_page, image_id,)
    await message.answer("Баннер добавлен/изменен✅", reply_markup=kb.admin_main)
    await state.clear()


# ловим некоррекный ввод
@admin_router.message(AddItemBanner.image)
async def add_banner2(message: Message):
    await message.answer("Отправьте изобржаение баннера или нажмите \"Отмена\"❌",
                         reply_markup=kb.admin_cancel)

#########################################################################################


######################### FSM для дабавления/изменения медиа админом ###################

class AddItem(StatesGroup):
    sub_category = State()
    item_media = State()
    media_text = State()

    item_for_change = None

    sub_category_filter = None

    texts = {
        'AddItem:item_media': "Отправьте медиа снова🔁",
        'AddItem:media_text': "Отправьте текст к медиа снова🔁",
    }


@admin_router.callback_query(StateFilter(None), F.data.startswith("change_"))
async def edit_item_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):

    item_id = callback.data.split("_")[-1]

    item_for_change = await orm_get_item(session, int(item_id))

    AddItem.item_for_change = item_for_change
    AddItem.sub_category_filter = item_for_change.sub_category_id

    await callback.message.answer((f'Отправьте изображение📷' if AddItem.sub_category_filter not in [2, 7]
                                   else 'Отправьте видео🎥'), reply_markup=kb.admin_cancel)

    await state.set_state(AddItem.item_media)


# Становимся в состояние ожидания выбора категории
@admin_router.message(StateFilter(None), F.text == 'Добавить медиа➕')
async def add_item(message: Message, state: FSMContext, session: AsyncSession):
    await message.answer(
        'Выберите...',
        reply_markup=kb.admin_cancel,
    )
    sub_categories = await redis_db.get_sub_categories_dict_admin()

    if sub_categories is None:
        sub_categories = await orm_get_sub_categories_admin(session)
        await redis_db.set_sub_categories_list_admin(sub_categories)

    btns = {sub_category.name: str(sub_category.id) for sub_category in sub_categories}
    await message.answer("...подкатегорию⭕",
                         reply_markup=get_inline_keyboard(btns=btns))
    await state.set_state(AddItem.sub_category)


# Хендлер отмены и сброса состояния должен быть всегда именно здесь,
# после того, как только встали в состояние номер 1 (элементарная очередность фильтров)
@admin_router.message(StateFilter("*"), F.text == "Отмена❌")
async def cancel(message: Message, state: FSMContext) -> None:
    current_state = state.get_state()

    if current_state is None:
        return
    if AddItem.item_for_change:
        AddItem.item_for_change = None

    await state.clear()
    await message.answer("Действия отменены✅", reply_markup=kb.admin_main)


# Полезная реализация кнопки назад по состояниям
@admin_router.message(StateFilter("*"), F.text == "Назад🔙")
async def back_step(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if isinstance(AddItem.sub_category_filter, int) and current_state == AddItem.item_media:
        await message.answer("Нет шага назад, выполните текущий шаг или нажмите \"Отмена\"❌.",
                             reply_markup=kb.admin_cancel)
        return

    elif current_state == AddItem.item_media and AddItem.sub_category_filter:
        await state.set_state(AddItem.sub_category)
        await message.answer("Выберите подкатегорию снова⏫")
        return

    elif current_state == AddItem.sub_category:
        await message.answer("Нет шага назад, выполните текущий шаг или нажмите \"Отмена\"❌.",
                             reply_markup=kb.admin_cancel)
        return

    previous = None
    for step in AddItem.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(AddItem.texts[previous.state], reply_markup=kb.admin_back_cancel)
            return
        previous = step


@admin_router.callback_query(AddItem.sub_category)
async def sub_category_choice(callback: CallbackQuery, state: FSMContext,
                              session: AsyncSession):
    if int(callback.data) in [2, 7]:
        AddItem.sub_category_filter = 'video'
    else:
        AddItem.sub_category_filter = 'photo'

    sub_categories = await redis_db.get_sub_categories_dict_admin()

    if sub_categories is None:
        sub_categories = await orm_get_sub_categories_admin(session)
        await redis_db.set_sub_categories_list_admin(sub_categories)

    if int(callback.data) in [sub_category.id for sub_category in sub_categories]:
        await callback.answer()
        await state.update_data(sub_category_id=callback.data)
        await callback.message.answer((f'Отправьте изображение📷' if AddItem.sub_category_filter == 'photo'
                                       else 'Отправьте видео🎥'), reply_markup=kb.admin_back_cancel)
    else:
        await callback.message.answer('Выберите подкатегорию из кнопок⏫')
        await callback.answer()
    await state.set_state(AddItem.item_media)


@admin_router.message(AddItem.sub_category)
async def error(message: Message):
    await message.answer('Следуйте инструкциям❗')


@admin_router.message(AddItem.item_media, or_f(F.text, F.photo))
async def add_item_media(message: Message, state: FSMContext) -> None:

    if message.text or message.photo:

        if message.text and message.text == ".":
            if AddItem.item_for_change:
                await state.update_data(item_media=AddItem.item_for_change.item_media)
            else:
                await message.answer(
                    'Следуйте инструкциям❗',
                )
        elif AddItem.sub_category_filter == 'photo':
            await state.update_data(item_media=message.photo[-1].file_id)

            await message.answer(
                'Отправьте текст к изображению🖊',
                reply_markup=kb.admin_back_cancel,
            )
            await state.set_state(AddItem.media_text)

        elif isinstance(AddItem.sub_category_filter, int):
            await state.update_data(item_media=message.photo[-1].file_id)

            await message.answer(
                'Отправьте текст к изображению🖊',
                reply_markup=kb.admin_back_cancel,
            )
            await state.set_state(AddItem.media_text)

        else:
            await message.answer(
                'Следуйте инструкциям❗',
                )


@admin_router.message(AddItem.item_media, or_f(F.text, F.video))
async def add_item_media(message: Message, state: FSMContext) -> None:

    if message.text or message.video:

        if message.text and message.text == ".":
            if AddItem.item_for_change:
                await state.update_data(item_media=AddItem.item_for_change.item_media)
            else:
                await message.answer(
                    'Следуйте инструкциям❗',
                )
        elif AddItem.sub_category_filter == 'video':
            await state.update_data(item_media=message.video.file_id)

            await message.answer(
                'Отправьте текст к видео🖊',
                reply_markup=kb.admin_back_cancel,
            )
            await state.set_state(AddItem.media_text)

        elif isinstance(AddItem.sub_category_filter, int):
            await state.update_data(item_media=message.photo[-1].file_id)

            await message.answer(
                'Отправьте текст к видео🖊',
                reply_markup=kb.admin_back_cancel,
            )
            await state.set_state(AddItem.media_text)

        else:
            await message.answer(
                'Следуйте инструкциям❗',
            )


@admin_router.message(AddItem.item_media)
async def error(message: Message) -> None:
    await message.answer(
        'Следуйте инструкциям❗',
    )


@admin_router.message(AddItem.media_text, F.text)
async def add_media_text(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if message.text == "." and AddItem.item_for_change:
        await state.update_data(media_text=AddItem.item_for_change.media_text)
    else:
        await state.update_data(media_text=message.text)
    data = await state.get_data()
    try:
        if AddItem.item_for_change:
            await orm_update_item(session, AddItem.item_for_change.id, data)
            await message.answer("Медиа изменено✅", reply_markup=kb.admin_main)
        else:
            await orm_add_item(session, data)
            await message.answer("Медиа добавлено✅", reply_markup=kb.admin_main)

        await state.clear()
        
    except Exception as e:
        await message.answer(f"Ошибка добавления медиа: \n\n{e}❗",
                             reply_markup=kb.admin_main)
        print(e)
        await state.clear()

    AddItem.item_for_change = None
    AddItem.sub_category_filter = None


@admin_router.message(AddItem.media_text)
async def error(message: Message) -> None:
    await message.answer(
        'Следуйте инструкциям❗',
    )
