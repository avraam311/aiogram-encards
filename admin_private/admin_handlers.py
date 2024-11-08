import sqlalchemy
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
                               orm_get_sub_categories_admin, orm_get_sub_category,
                               orm_update_sub_category, orm_delete_sub_category, orm_add_sub_category,
                               orm_get_categories, orm_get_banner, orm_get_sub_categories_user)
from common.get_keyboard_func import get_inline_keyboard
from cache import Cache
import config


config = config.Config()

redis_db = Cache(username=config.redis_username, password=config.redis_password,
                 host=config.redis_host, port=config.redis_port, db=config.redis_db)

admin_router = Router()
admin_router.message.filter(IsAdmin())


@admin_router.message(Command("admin"))
async def admin_features(message: Message, state: FSMContext):
    await message.answer("Что хотите сделать❓", reply_markup=kb.admin_main)
    await state.clear()


@admin_router.message(F.text == 'Просмотреть медиа🕶')
async def admin_features(message: Message, session: AsyncSession):
    sub_categories = redis_db.get_sub_categories_list_admin()

    if sub_categories is None:
        sub_categories = await orm_get_sub_categories_admin(session)
        redis_db.set_sub_categories_list_admin(sub_categories)

    btns = {sub_category[1]: f'sub_category_{sub_category[0]}' for sub_category in sub_categories}
    await message.answer("Выберите подкатегорию:", reply_markup=get_inline_keyboard(btns=btns))


@admin_router.message(F.text == 'Просмотреть подкатегории👓')
async def admin_features(message: Message, session: AsyncSession):
    sub_categories = redis_db.get_sub_categories_list_admin()

    if sub_categories is None:
        sub_categories = await orm_get_sub_categories_admin(session)
        redis_db.set_sub_categories_list_admin(sub_categories)

    for sub_category in sub_categories:
        sub_category_id = sub_category[0]
        await message.answer(
            sub_category[1],
            reply_markup=get_inline_keyboard(
                btns={
                    "Удалить🧺": f"sub_delete_{sub_category_id}",
                    "Изменить✅": f"sub_change_{sub_category_id}",
                },
                sizes=(2,)
            ),
        )
    await message.answer("ОК, вот список⏫")


@admin_router.message(F.text == "Ничего🌊")
async def nth(message: Message, state: FSMContext) -> None:
    await message.answer(
        message.text,
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.clear()


@admin_router.callback_query(F.data.startswith('sub_category_'))
async def starring_at_item(callback: CallbackQuery, session: AsyncSession):
    if int(callback.data.split('_')[-1]) in [2, 7]:
        answer_photo_or_video = callback.message.answer_video
    else:
        answer_photo_or_video = callback.message.answer_photo

    sub_category_id = callback.data.split('_')[-1]

    items = await orm_get_items(session, int(sub_category_id))

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


@admin_router.callback_query(F.data.startswith("sub_delete_"))
async def sub_delete_category_callback(callback: CallbackQuery, session: AsyncSession):
    sub_category_id = callback.data.split("_")[-1]
    if sub_category_id == '13':
        await callback.message.answer("Нельзя удалить подкатегорию\"Другое🟢\"!")
        return
    try:
        await orm_delete_sub_category(session, int(sub_category_id))
        sub_categories = await orm_get_sub_categories_admin(session)
        redis_db.set_sub_categories_list_admin(sub_categories)
        redis_db.delete_sub_category_user(sub_category_id)
        await callback.message.answer("Удаление прошло успешно✅")
        await callback.message.delete()
    except sqlalchemy.exc.IntegrityError:
        await callback.message.answer("Нельзя удалить подкатегорию, в которой есть медиа\n\n"
                                      "Сначала перенесите медиа в другую подкатегорию❗")


# FSM для загрузки/изменения баннеров ############################

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
    if not message.caption:
        await message.answer("Отправьте изображение вместе с названием страницы")
        return
    for_page = message.caption.strip()
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    if for_page not in pages_names:
        await message.answer(f"Введите нормальное название страницы, например:\
                         \n\n{', '.join(pages_names)}")
        return
    await orm_change_banner_image(session, for_page, image_id,)
    banner = await orm_get_banner(session, for_page)
    banner_for_redis = list()
    banner_for_redis.append(banner.image)
    banner_for_redis.append(banner.description)
    banner_for_redis = 'banner'.join(banner_for_redis)
    redis_db.set_banner(for_page, banner_for_redis)
    await message.answer("Баннер добавлен/изменен✅", reply_markup=kb.admin_main)
    await state.clear()


# ловим некоррекный ввод
@admin_router.message(AddItemBanner.image)
async def add_banner2(message: Message):
    await message.answer("Отправьте изобржаение баннера или нажмите \"Отмена\"❌",
                         reply_markup=kb.admin_cancel)
#########################################################################################


# FSM для дабавления/изменения медиа админом ###################

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


# Становимся в состояние ожидания выбора подкатегории
@admin_router.message(StateFilter(None), F.text == 'Добавить медиа➕')
async def add_item(message: Message, state: FSMContext, session: AsyncSession):
    await message.answer(
        'Выберите...',
        reply_markup=kb.admin_cancel,
    )
    sub_categories = redis_db.get_sub_categories_list_admin()

    if sub_categories is None:
        sub_categories = await orm_get_sub_categories_admin(session)
        redis_db.set_sub_categories_list_admin(sub_categories)

    btns = {sub_category[1]: str(sub_category[0]) for sub_category in sub_categories}
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

    if (isinstance(AddItem.sub_category_filter, int) and current_state == AddItem.item_media)\
            or (current_state == AddSubCategory.category)\
            or (current_state == AddItem.sub_category):
        await message.answer("Нет шага назад, выполните текущий шаг или нажмите \"Отмена\"❌.",
                             reply_markup=kb.admin_cancel)
        return

    elif current_state == AddItem.item_media and AddItem.sub_category_filter:
        await state.set_state(AddItem.sub_category)
        await message.answer("Выберите подкатегорию снова⏫")
        return

    elif current_state == AddSubCategory.sub_category:
        await state.set_state(AddSubCategory.category)
        await message.answer("Выберите категорию снова⏫")
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

    sub_categories = redis_db.get_sub_categories_list_admin()

    if sub_categories is None:
        sub_categories = await orm_get_sub_categories_admin(session)
        redis_db.set_sub_categories_list_admin(sub_categories)

    if int(callback.data) in [sub_category[0] for sub_category in sub_categories]:
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
        await message.answer(f"Ошибка добавления медиа❗",
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


# FSM для дабавления/изменения подкатегорий админом ###################

class AddSubCategory(StatesGroup):
    category = State()
    sub_category = State()

    sub_category_for_change = None


@admin_router.callback_query(StateFilter(None), F.data.startswith("sub_change_"))
async def edit_sub_category_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    sub_category_id = callback.data.split("_")[-1]
    if sub_category_id == '13':
        await callback.message.answer("Нельзя изменить подкатегорию\"Другое🟢\"!")
        return

    sub_category_for_change = await orm_get_sub_category(session, int(sub_category_id))

    AddSubCategory.sub_category_for_change = sub_category_for_change

    await callback.message.answer(f'Отправьте название подкатегории🖊',
                                  reply_markup=kb.admin_cancel)

    await state.set_state(AddSubCategory.sub_category)


# Становимся в состояние ожидания выбора категории
@admin_router.message(StateFilter(None), F.text == 'Добавить подкатегорию➕')
async def add_sub_category(message: Message, state: FSMContext, session: AsyncSession):
    await message.answer(
        'Выберите...',
        reply_markup=kb.admin_cancel,
    )
    categories = redis_db.get_categories_list()

    if categories is None:
        categories = await orm_get_categories(session)
        redis_db.set_categories_list(categories)

    btns = {category[1]: 'category_'+str(category[0]) for category in categories}
    await message.answer("...категорию⭕",
                         reply_markup=get_inline_keyboard(btns=btns))
    await state.set_state(AddSubCategory.category)


# Хендлер отмены состояния должен быть всегда именно здесь,
# после того, как только встали в состояние номер 1 (элементарная очередность фильтров)
@admin_router.message(StateFilter("*"), F.text == "Отмена❌")
async def cancel(message: Message, state: FSMContext) -> None:
    current_state = state.get_state()

    if current_state is None:
        return
    if AddSubCategory.sub_category_for_change:
        AddSubCategory.sub_category_for_change = None

    await state.clear()
    await message.answer("Действия отменены✅", reply_markup=kb.admin_main)


@admin_router.callback_query(AddSubCategory.category)
async def category_choice(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    categories = redis_db.get_categories_list()

    if categories is None:
        categories = await orm_get_categories(session)
        redis_db.set_categories_list(categories)

    category_id = int(callback.data.split('_')[-1])

    if int(category_id) in [category[0] for category in categories]:
        await callback.answer()
        await state.update_data(category_id=category_id)
        await callback.message.answer(f'Отправьте название подкатегории🖊',
                                      reply_markup=kb.admin_back_cancel)
    else:
        await callback.message.answer('Выберите категорию из кнопок⏫')
        await callback.answer()
    await state.set_state(AddSubCategory.sub_category)


@admin_router.message(AddSubCategory.category)
async def error(message: Message):
    await message.answer('Следуйте инструкциям❗')


@admin_router.message(AddSubCategory.sub_category, F.text)
async def add_sub_category(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if AddSubCategory.sub_category_for_change and message.text != '.':
        await state.update_data(category_id=AddSubCategory.sub_category_for_change.category_id)
        await state.update_data(sub_category=message.text)
    elif AddSubCategory.sub_category_for_change and message.text == '.':
        await state.update_data(category_id=AddSubCategory.sub_category_for_change.category_id)
        await state.update_data(sub_category=AddSubCategory.sub_category_for_change.name)
    else:
        await state.update_data(sub_category=message.text)
    data = await state.get_data()
    try:
        if AddSubCategory.sub_category_for_change:
            await orm_update_sub_category(session, AddSubCategory.sub_category_for_change.id, data)
            sub_categories = await orm_get_sub_categories_admin(session)
            redis_db.set_sub_categories_list_admin(sub_categories)
            sub_categories = await orm_get_sub_categories_user(session,
                                                               str(AddSubCategory.sub_category_for_change.category_id),)
            redis_db.set_sub_categories_list_user(sub_categories,
                                                  str(AddSubCategory.sub_category_for_change.category_id))
            await message.answer("Подкатегория изменена✅", reply_markup=kb.admin_main)
        else:
            await orm_add_sub_category(session, data)
            sub_categories = await orm_get_sub_categories_admin(session)
            redis_db.set_sub_categories_list_admin(sub_categories)
            sub_categories = await orm_get_sub_categories_user(session,
                                                               data["category_id"],)
            redis_db.set_sub_categories_list_user(sub_categories,
                                                  data["category_id"],)
            await message.answer("Подкатегория добавлена✅", reply_markup=kb.admin_main)

        await state.clear()

    except Exception as e:
        await message.answer(f"Ошибка добавления подкатегории❗",
                             reply_markup=kb.admin_main)
        await message.answer(str(e))
        await message.answer(str(e))
        print(e)
        await state.clear()

    AddSubCategory.sub_category_for_change = None


@admin_router.message(AddSubCategory.sub_category)
async def error(message: Message) -> None:
    await message.answer(
        'Следуйте инструкциям❗',
    )
