import asyncio
import json
import sys

from aiogram import Bot, Dispatcher

from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from src.settings import get_settings, Settings
from src.telegram.handlers import register_handlers

import logging as log

from src.telegram.handlers.commands import base_router
from src.telegram.handlers.payments import payment_router

cfg: Settings = get_settings()

dp = Dispatcher()
bot = Bot(cfg.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp.include_router(base_router)
dp.include_router(payment_router)

# Пример ограничения доступа к боту только для определенных пользователей
# acl = (111111111,)
# admin_only = lambda message: message.from_user.id not in acl
# @dp.message_handler(admin_only, content_types=['any'])
# async def handle_unwanted_users(message: types.Message):
#     await config.bot.delete_message(message.chat.id, message.message_id)
#     return


async def start_telegram() -> None:
    # webapp_info = WebAppInfo(url=cfg.webapp_url)
    webhook_info = await bot.get_webhook_info()

    # if webhook_info.url != cfg.webhook_url:
    await bot.set_webhook(url='')
    await bot.set_webhook(
        url=cfg.webhook_url,
        secret_token=cfg.tg_secret_token,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
        max_connections=40 if cfg.debug else 100,
    )

    # Назначаем действие для кнопки меню (запускаем webapp)
    # menu_button = MenuButtonWebApp(text='Play', web_app=webapp_info)
    # await bot.set_chat_menu_button(menu_button=menu_button)

    # Задаем список команд
    commands = [
        BotCommand(command="/id", description="👋 Get my ID"),
        BotCommand(command="/get_referral_link", description="Get referral link"),
        BotCommand(command="/test_pay", description="Test payment"),
        BotCommand(command="/refund_pay", description="Test refund"),
        BotCommand(command="/paysupport", description="refund FAQ"),
    ]
    await bot.set_my_commands(commands)


async def end_telegram():
    await bot.set_webhook(url='')
    await bot.close()


dp.startup.register(start_telegram)
dp.shutdown.register(end_telegram)


# для локальной разработки
async def main() -> None:
    await dp.start_polling(bot)
    log.info('Telegram bot is running!')


if __name__ == '__main__':
    try:
        log.basicConfig(level=log.INFO, stream=sys.stdout)
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info('Exit')
