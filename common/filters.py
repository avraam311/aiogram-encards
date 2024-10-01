from aiogram.filters import Filter
from aiogram import Bot
from aiogram.types import Message

import os


class IsAdmin(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message, bot: Bot) -> bool:
        if message.from_user.id != int(os.getenv('ADMIN_ID')):
            await message.delete()
            return False
        return True
