import asyncio
import os
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())


import logging
import platform

from aiogram import Bot, Dispatcher
from aiogram import types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from user_private.handlers import user_router
from admin_private.admin_handlers import admin_router
from user_private.payment import payment_router
from common.commands import private
from database.engine import create_db, drop_all, session_maker
from middlewares.db import DataBaseSession


bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()

dp.include_routers(user_router, admin_router, payment_router)


async def on_startup(bot):

    run_param = False
    if run_param:
        await drop_all()

    await create_db()


async def on_shutdown(bot):
    pass


async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await bot.set_my_description('Ассаляму 1аляйкум, это бот для изучения английского языка максимально эффективно,'
                                 'пользы и удачи!💟')
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    try:
        logging.basicConfig(level=logging.INFO)
        logging.info('Бот включен')
        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')
