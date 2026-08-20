import logging
import asyncio
import os
import time

from aiogram import Dispatcher, Bot
from aiogram.enums import ParseMode
from aiogram.types import ErrorEvent
from aiogram.client.default import DefaultBotProperties
from aiogram_dialog import setup_dialogs
from fluentogram import TranslatorHub
from aiogram.client.session.aiohttp import AiohttpSession


from config_data.config import Config, load_config
import dialogs.dialog as dialog
from i18n.translator_hub import create_translator_hub
from middlewares.i18n import TranslatorRunnerMiddleware
from handlers import user_handlers
from services.retry_message_manager import RetryMessageManager

# ИСПРАВЛЕНО: Оставляем только async_session
from database.db import async_session

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] #%(levelname)-8s %(filename)s:'
                                                '%(lineno)d - %(name)s - %(message)s')

logger = logging.getLogger(__name__)

UPLOADS_DIR = 'data/uploads'
MAX_AGE_DAYS = 4
CLEANUP_INTERVAL_HOURS = 24


async def cleanup_old_uploads():
    """Раз в сутки удаляет файлы из data/uploads старше MAX_AGE_DAYS."""
    while True:
        try:
            now = time.time()
            max_age_sec = MAX_AGE_DAYS * 24 * 3600
            removed = 0
            for filename in os.listdir(UPLOADS_DIR):
                path = os.path.join(UPLOADS_DIR, filename)
                if not os.path.isfile(path):
                    continue
                if now - os.path.getmtime(path) > max_age_sec:
                    try:
                        os.remove(path)
                        removed += 1
                    except OSError:
                        logger.exception('Не удалось удалить файл %s', path)
            if removed:
                logger.info('Очистка uploads: удалено файлов старше %s дн.: %s', MAX_AGE_DAYS, removed)
        except Exception:
            logger.exception('Ошибка в задаче очистки uploads')
        await asyncio.sleep(CLEANUP_INTERVAL_HOURS * 3600)


async def main():
    logger.info('Бот запускается')

    config: Config = load_config()

    session = AiohttpSession(
        proxy=config.proxy,
        # Если прокси БЕЗ авторизации — убери proxy_auth
        # proxy_auth=BasicAuth(login="your_login", password="your_password")
    )

    bot = Bot(
        token=config.tg_bot.token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    translator_hub: TranslatorHub = create_translator_hub()

    # Кладем в workflow_data, чтобы hub и сессии были доступны и в фоновых
    # событиях диалогов (bg.done()/bg.switch_to), которые распространяются через
    # dp.propagate_event(**self.dp.workflow_data)
    dp.workflow_data['_translator_hub'] = translator_hub
    dp.workflow_data['session_maker'] = async_session

    # Подключаем роутеры
    dp.include_routers(user_handlers.user_router, dialog.start_dialog, dialog.select_collection, dialog.get_photo_user, dialog.forming_cards)

    dp.update.middleware(TranslatorRunnerMiddleware())

    # Глобальная обработка ошибок: не даём ронять поллинг
    @dp.errors()
    async def on_update_error(event: ErrorEvent):
        logger.exception('Ошибка при обработке апдейта: %s', event.exception)

    # Важно: setup_dialogs всегда в конце, после регистрации всех роутеров
    setup_dialogs(dp, message_manager=RetryMessageManager())

    os.makedirs(UPLOADS_DIR, exist_ok=True)

    # Автосоздание таблиц (идемпотентно, существующие не трогает)
    from database.db import Base, engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Фоновая очистка uploads: при старте и далее раз в сутки
    asyncio.create_task(cleanup_old_uploads())

    # ИСПРАВЛЕНО: Передаем фабрику сессий БД (session_maker), чтобы ловить её в хэндлерах
    await dp.start_polling(
        bot,
        _translator_hub=translator_hub,
        session_maker=async_session
    )

if __name__ == '__main__':
    # ИСПРАВЛЕНО: Правильная точка входа
    asyncio.run(main())