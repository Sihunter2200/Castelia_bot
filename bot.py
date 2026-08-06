import logging
import asyncio

from aiogram import Dispatcher, Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram_dialog import setup_dialogs
from fluentogram import TranslatorHub
from aiogram.client.session.aiohttp import AiohttpSession


from config_data.config import Config, load_config
import dialogs.dialog as dialog
from i18n.translator_hub import create_translator_hub
from middlewares.i18n import TranslatorRunnerMiddleware
from handlers import user_handlers

# ИСПРАВЛЕНО: Оставляем только async_session
from database.db import async_session

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] #%(levelname)-8s %(filename)s:'
                                                '%(lineno)d - %(name)s - %(message)s')

logger = logging.getLogger(__name__)

async def main():
    logger.info('Бот запускается')

    config: Config = load_config()

    session = AiohttpSession(
        proxy="",
        # Если прокси БЕЗ авторизации — убери proxy_auth
        # proxy_auth=BasicAuth(login="your_login", password="your_password")
    )

    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    translator_hub: TranslatorHub = create_translator_hub()

    # Подключаем роутеры
    dp.include_routers(dialog.start_dialog, user_handlers.user_router)

    dp.update.middleware(TranslatorRunnerMiddleware())

    # Важно: setup_dialogs всегда в конце, после регистрации всех роутеров
    setup_dialogs(dp)

    # ИСПРАВЛЕНО: Передаем фабрику сессий БД (session_maker), чтобы ловить её в хэндлерах
    await dp.start_polling(
        bot,
        _translator_hub=translator_hub,
        session_maker=async_session
    )

if __name__ == '__main__':
    # ИСПРАВЛЕНО: Правильная точка входа
    asyncio.run(main())