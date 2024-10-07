from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery

import os


payment_router = Router()


PRICE = LabeledPrice(label='Подписка на 1 месяц', amount=99*100)


@payment_router.message(Command('buy_spec_pack'))
async def commamd_buy_spec_pack(message: Message, bot: Bot):
    if os.getenv('PAYMENTS_TOKEN').split(':')[1] == 'TEST':
        await message.answer('ТЕСТОВЫЙ ПЛАТЕЖ!!!')

    await bot.send_invoice(chat_id=message.from_user.id,
                           title='Покупка спец. пакета',
                           description='Активация подписки на спец. пакет на 1 месяц',
                           provider_token=os.getenv('PAYMENTS_TOKEN'),
                           currency='rub',
                           photo_url='https://trikky.ru/krasivye-kartinki-880042.html',
                           photo_width=800,
                           photo_height=450,
                           photo_size=100,
                           is_flexible=False,
                           prices=[PRICE],
                           start_parameter='one-month-subscription',
                           payload='test-invoice-payload',
                           max_tip_amount=5,
                           suggested_tip_amounts=[1, 2, 3, 4],
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
async def successful_payment(message: Message):
    payment_message = (f'Спасибо за оплату {message.successful_payment.total_amount // 100} '
                       f'{message.successful_payment.currency}.')
    await message.answer(payment_message)
