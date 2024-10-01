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
                               orm_get_sub_categories)
from common.get_keyboard_func import get_inline_keyboard

admin_router = Router()
admin_router.message.filter(IsAdmin())


@admin_router.message(Command("admin"))
async def admin_features(message: Message):
    await message.answer("Что хотите сделать?", reply_markup=kb.admin_main)


@admin_router.message(F.text == 'Просмотреть')
async def admin_features(message: Message, session: AsyncSession):
    sub_categories = await orm_get_sub_categories(session)
    btns = {sub_category.name: f'sub_category_{sub_category.id}' for sub_category in sub_categories}
    await message.answer("Выберите подподкатегорию", reply_markup=get_inline_keyboard(btns=btns))


@admin_router.message(F.text == "Ничего")
async def nth(message: Message) -> None:
    await message.answer(
        message.text,
        reply_markup=ReplyKeyboardRemove(),
    )


@admin_router.callback_query(F.data.startswith('sub_category_'))
async def starring_at_item(callback: CallbackQuery, session: AsyncSession):
    sub_category_id = callback.data.split('_')[-1]
    for item in await orm_get_items(session, int(sub_category_id)):
        await callback.message.answer_document(
            item.item_media,
            caption=f"<strong>{item.media_text}</strong>\n",
            reply_markup=get_inline_keyboard(
                btns={
                    "Удалить": f"delete_{item.id}",
                    "Изменить": f"change_{item.id}",
                },
                sizes=(2,)
            ),
        )
    await callback.answer()
    await callback.message.answer("ОК, вот список ⏫")


@admin_router.callback_query(F.data.startswith("delete_"))
async def delete_item_callback(callback: CallbackQuery, session: AsyncSession):
    item_id = callback.data.split("_")[-1]
    await orm_delete_item(session, int(item_id))

    await callback.message.answer("Удаление прошло успешно")


################# Микро FSM для загрузки/изменения баннеров ############################

class AddItemBanner(StatesGroup):
    image = State()


# Отправляем перечень информационных страниц бота и становимся в состояние отправки photo
@admin_router.message(StateFilter(None), F.text == 'Добавить/Изменить баннер')
async def add_image2(message: Message, state: FSMContext, session: AsyncSession):
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    await message.answer(f"Отправьте фото баннера.\n\nВ описании укажите для какой страницы:\
                         \n\n{', '.join(pages_names)}",
                         reply_markup=kb.admin_cancel)
    await state.set_state(AddItemBanner.image)


@admin_router.message(AddItemBanner.image, F.text == 'Отмена')
async def add_banner(message: Message, state: FSMContext):
    await message.answer(message.text, reply_markup=kb.admin_main)
    await state.clear()


# Добавляем/изменяем изображение в таблице (там уже есть записанные страницы по именам:
# main, read!, catalog, sub_catalog, spec_pack
@admin_router.message(AddItemBanner.image, F.photo)
async def add_banner(message: Message, state: FSMContext, session: AsyncSession):
    image_id = message.photo[-1].file_id
    for_page = message.caption.strip()
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    if for_page not in pages_names:
        await message.answer(f"Введите нормальное название страницы, например:\
                         \n{', '.join(pages_names)}")
        return
    await orm_change_banner_image(session, for_page, image_id,)
    await message.answer("Баннер добавлен/изменен.", reply_markup=kb.admin_main)
    await state.clear()


# ловим некоррекный ввод
@admin_router.message(AddItemBanner.image)
async def add_banner2(message: Message):
    await message.answer("Отправьте фото баннера или отмена")

#########################################################################################


######################### FSM для дабавления/изменения медиа админом ###################

class AddItem(StatesGroup):
    item_media = State()
    sub_category = State()
    media_text = State()

    item_for_change = None

    sub_category_filter = None

    # это свойство мне в данной реализации не нужно, но я его добавил для изучения синтаксиса
    # а так у меня к каждому состоянию привязана всегда одна и та же клавиатура
    keyboards = {
        'AddItem:item_media': kb.admin_back_cancel,
        'AddItem:media_text': kb.admin_back_cancel,
    }

    texts = {
        'AddItem:item_media': "Отправьте медиа снова",
        'AddItem:media_text': "Напишите текст фильма снова",
    }


@admin_router.callback_query(StateFilter(None), F.data.startswith("edit_"))
async def edit_item_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):

    item_id = callback.data.split("_")[-1]

    item_for_change = await orm_get_item(session, int(item_id))

    AddItem.item_for_change = item_for_change

    await callback.message.answer(
        'Отправьте фото фильма',
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(AddItem.item_media)


# Становимся в состояние ожидания выбора категории
@admin_router.message(StateFilter(None), F.text == 'Добавить медиа')
async def add_item(message: Message, state: FSMContext, session: AsyncSession):
    await state.set_state(AddItem.item_media)

    await message.answer(
        'Выберите...',
        reply_markup=kb.admin_back_cancel,
    )
    sub_categories = await orm_get_sub_categories(session)
    btns = {sub_category.name: str(sub_category.id) for sub_category in sub_categories}
    await message.answer("...подкатегорию",
                         reply_markup=get_inline_keyboard(btns=btns))
    await state.set_state(AddItem.sub_category)


# Хендлер отмены и сброса состояния должен быть всегда именно здесь,
# после того, как только встали в состояние номер 1 (элементарная очередность фильтров)
@admin_router.message(StateFilter("*"), F.text == "Отмена")
async def cancel(message: Message, state: FSMContext) -> None:
    current_state = state.get_state()

    if current_state is None:
        return
    if AddItem.item_for_change:
        AddItem.item_for_change = None
    await state.clear()
    await message.answer(
        message.text,
        reply_markup=kb.admin_main,
    )

    await state.clear()
    await message.answer("Действия отменены", reply_markup=kb.admin_main)


# Вторая реализация кнопки назад по состояниям
# Потом оставлю лучший вариант
@admin_router.message(StateFilter("*"), F.text == "Назад")
async def back_step(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state == AddItem.item_media:
        await message.answer("Нет шага назад, выполните текущий шаг или нажмите 'Отмена'")
        return

    previous = None
    for step in AddItem.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(AddItem.texts[previous.state], reply_markup=AddItem.keyboards[previous.state])
            return
        previous = step


@admin_router.callback_query(AddItem.sub_category)
async def sub_category_choice(callback: CallbackQuery, state: FSMContext,
                          session: AsyncSession):
    chosen_sub_category = int(callback.data)
    if chosen_sub_category in [2, 7]:
        AddItem.sub_category_filter = F.video
    else:
        AddItem.sub_category_filter = F.photo

    if int(callback.data) in [sub_category.id for sub_category in
                              await orm_get_sub_categories(session)]:
        await callback.answer()
        await state.update_data(sub_category_id=callback.data)
        await callback.message.answer('Отправьте медиа', reply_markup=kb.admin_back_cancel)
    else:
        await callback.message.answer('Выберите подкатегорию из кнопок')
        await callback.answer()
    await state.set_state(AddItem.item_media)


@admin_router.message(AddItem.sub_category)
async def error(message: Message):
    await message.answer('Следуйте инструкциям!')


sub_category_filter = AddItem.sub_category_filter


@admin_router.message(AddItem.item_media, or_f(F.video, F.text == "."))
async def add_item_media(message: Message, state: FSMContext) -> None:
    # if AddItem.sub_category_filter == 'photo':
    #     if message.text and message.text == ".":
    #         await state.update_data(item_media=AddItem.item_for_change.item_media)
    #     elif message.photo:
    #         await state.update_data(item_media=message.photo[-1].file_id)
    #
    # elif AddItem.sub_category_filter == 'video':
    if message.text and message.text == ".":
        await state.update_data(item_media=AddItem.item_for_change.item_media)
    else:
        await state.update_data(item_media=message.video.file_id)

    await message.answer(
        'Отправьте текст к медиа',
        reply_markup=kb.admin_back_cancel,
    )
    AddItem.sub_category_filter = None
    await state.set_state(AddItem.media_text)


@admin_router.message(AddItem.item_media)
async def error(message: Message) -> None:
    await message.answer(
        'Следуйте инструкциям!',
    )


@admin_router.message(AddItem.media_text, or_f(F.text, F.text == "."))
async def add_media_text(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if message.text == ".":
        await state.update_data(media_text=AddItem.item_for_change.media_text)
    else:
        await state.update_data(media_text=message.text)
    data = await state.get_data()
    try:
        if AddItem.item_for_change:
            await orm_update_item(session, AddItem.item_for_change.id, data)
            await message.answer("Медиа изменено", reply_markup=kb.admin_main)
        else:
            await orm_add_item(session, data)
            await message.answer("Медиа добавлено", reply_markup=kb.admin_main)

        await state.clear()
        
    except Exception as e:
        await message.answer(f"Ошибка добавления медиа: {e}",
                             reply_markup=kb.admin_main)
        print(e)
        await state.clear()

    AddItem.item_for_change = None


@admin_router.message(AddItem.media_text)
async def error(message: Message) -> None:
    await message.answer(
        'Следуйте инструкциям!',
    )
