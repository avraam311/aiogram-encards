from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery

from sqlalchemy.ext.asyncio import AsyncSession
import time
import datetime

from database.requests import orm_set_user_spec_pack, orm_status_user_spec_pack, orm_get_user_spec_pack

import os


payment_router = Router()


PRICE = LabeledPrice(label='Подписка на 1 месяц', amount=99*100)


def days_to_seconds(days):
    return days*24*60*60


def spec_pack_left_time(get_spec_pack_time):
    time_now = int(time.time())
    middle_time = int(get_spec_pack_time) - time_now

    if middle_time <= 0:
        return False
    else:
        dt = str(datetime.timedelta(seconds=middle_time))
        dt = dt.replace('days', 'дней')
        dt = dt.replace('day', 'день')
        dt = dt.replace('2 days', '2 дня')
        dt = dt.replace('3 days', '3 дня')
        dt = dt.replace('4 days', '4 дня')
        return dt


@payment_router.message(F.text == 'spec_pack')
@payment_router.message(Command('spec_pack'))
async def buy_spec_pack(message: Message, bot: Bot, session: AsyncSession):
    spec_pack_status = await orm_status_user_spec_pack(session, user_id=message.from_user.id)
    spec_pack_time = await orm_get_user_spec_pack(session, user_id=message.from_user.id)
    if spec_pack_status:
        await message.answer(text=f'У вас уже есть спец. пакет на '
                                  f'{spec_pack_left_time(spec_pack_time)}'
                                  f', просто наслаждайтесь!')
        return

    if os.getenv('PAYMENTS_TOKEN').split(':')[1] == 'TEST':
        await message.answer('ТЕСТОВЫЙ ПЛАТЕЖ!!!')

    await bot.send_invoice(chat_id=message.from_user.id,
                           title='Покупка спец. пакета',
                           description='Активация подписки на спец. пакет на 1 месяц',
                           provider_token=os.getenv('PAYMENTS_TOKEN'),
                           currency='rub',
                           photo_url='https://store-images.s-microsoft.com/image/apps.63187.9007199266299154.e6a7e317'
                                     '-b6a1-4b9b-b715-96b5a6f9d8e5.67cfe3e1-4d5e-44f0-943f-e4636346341f?h=210',
                           photo_width=800,
                           photo_height=450,
                           photo_size=100,
                           is_flexible=False,
                           prices=[PRICE],
                           start_parameter='one-month-subscription',
                           payload='test-invoice-payload',
                           max_tip_amount=5*100,
                           suggested_tip_amounts=[1*100, 2*100, 3*100, 4*100],
                           provider_data=None,
                           need_name=False,
                           need_email=False,
                           need_phone_number=False,
                           need_shipping_address=False,
                           send_phone_number_to_provider=False,
                           send_email_to_provider=False,
                           disable_notification=False,
                           protect_content=False,
                           reply_to_message_id=None,
                           allow_sending_without_reply=True,
                           reply_markup=None,
                           request_timeout=15,)


@payment_router.pre_checkout_query(lambda query: True)
async def f_pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@payment_router.message(F.successful_payment)
async def successful_payment(message: Message, session: AsyncSession):
    if message.successful_payment.invoice_payload == 'test-invoice-payload':
        payment_message = (f'Спасибо за оплату ({message.successful_payment.total_amount // 100} '
                           f'{message.successful_payment.currency}).'
                           f'\nПодписка на 1 месяц оформлена)')
        spec_pack_time = int(time.time()) + days_to_seconds(30)
        await message.answer(payment_message)
        await orm_set_user_spec_pack(session, user_id=message.from_user.id, spec_pack=spec_pack_time)
