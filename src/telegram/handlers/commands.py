import json

from aiogram import Router, types
from aiogram.filters import Command, Filter, CommandObject
from aiogram.types import (Message, BotCommand, WebAppInfo, LabeledPrice, InlineKeyboardButton)
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.game_api.services.user_service import UserService
from src.settings import get_settings
from src.telegram.bot import bot

from loguru import logger as log

cfg = get_settings()

base_router = Router(name=__name__)


@base_router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    await message.answer(f"Your ID: {message.from_user.id}")


@base_router.message(Command("start"))
async def start_handler(message: Message, command: CommandObject):
    try:
        args = command.args
        tg_user_id = str(message.from_user.id)

        if args:
            # Логика для обработки deep link
            if tg_user_id and tg_user_id != args:
                await UserService.create_or_update_user_by_telegram_id(message, args)
                await message.answer(f"Вы успешно зарегистрированы по реферальной ссылке")
            else:
                await message.answer("Нельзя пригласить самого себя.")

        else:
            # Логика для обычного вызова команды /start
            welcome_text = "Добро пожаловать! Нажмите на кнопку ниже для старта."
            builder = InlineKeyboardBuilder()
            button = InlineKeyboardButton(text="Играть", web_app=WebAppInfo(url=cfg.webapp_url))
            builder.add(button)

            await UserService.create_or_update_user_by_telegram_id(message, None)
            await message.answer(welcome_text, reply_markup=builder.as_markup())
    except Exception as e:
        log.exception(e)


@base_router.message(Command("get_referral_link"))
async def get_referral_link(message: Message) -> None:
    reflink = await create_start_link(
        bot=bot,
        payload=str(message.from_user.id),
        encode=False
    )
    await message.answer(f"Ваша пригласительная ссылка: {reflink}")


@base_router.message(Command("support"))
async def pay_support_handler(message: Message):
    await message.answer(
        text="Описание того, как сделать рефанд."
    )


@base_router.message(Command("test_pay"))
async def send_invoice_handler(message: Message):
    prices = [LabeledPrice(label="XTR", amount=1)]
    payload = dict(
        user_id=message.from_user.id,
        product_type='boost',
        product_id=1,
    )
    await message.answer_invoice(
        title="Тестовый товар",
        description="описание",
        prices=prices,
        provider_token="",
        payload=json.dumps(payload),
        currency="XTR",
        reply_markup=payment_keyboard(),
    )