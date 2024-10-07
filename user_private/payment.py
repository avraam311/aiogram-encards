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
                           photo_url='https://www.google.com/search?sca_esv=427163c40a0d98b7&q=%D0%BF%D1%80%D0%B5%D0%'
                                     'BC%D0%B8%D1%83%D0%BC+%D1%84%D0%BE%D1%82%D0%BE&udm=2&fbs=AEQNm0Cjmfui-wh8X_MyYW0'
                                     '4R9TpEz659VicRvdQoqLb32FEYtz9ghAES1yRtdnSWbgjSrKC1IfMtFTKUsdltxh9toINrzStdIlCBc'
                                     'eZl_foKvRSW9Tkt-sNYnmPo793dhPX8r63clcJh6cSvGw7O_CduM5FcId0Q-vu-R_OLitntAdM6EgP1'
                                     'N8MU8DF3jyLDjIuc8uxZ5qZoI6foDxnpVRQfebfOl_JUKxvpVRQWipraxzTga7rPjU&sa=X&sqi=2&v'
                                     'ed=2ahUKEwi00oSOsvyIAxXUi8MKHa9xDZsQtKgLegQIExAB#vhid=xdyuiN9xqh8fOM&vssid=mosa'
                                     'ic',
                           photo_width=416,
                           photo_height=234,
                           photo_size=416,
                           is_flexible=False,
                           prices=[PRICE],
                           start_parameter='one-month-subscription',
                           payload='test-invoice-payload',)


@payment_router.pre_checkout_query(lambda query: True)
async def f_pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@payment_router.message(F.successful_payment)
async def successful_payment(message: Message):
    await message.successful_payment
