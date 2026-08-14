import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter
from aiogram_dialog.api.entities import NewMessage, OldMessage
from aiogram_dialog.api.protocols import MessageNotModified
from aiogram_dialog.manager.message_manager import MessageManager
from aiogram.types import Message

logger = logging.getLogger(__name__)


class RetryMessageManager(MessageManager):
    def __init__(self, max_retry: int = 3, timeout: float = 0.5):
        super().__init__()
        self.max_retry = max_retry
        self.timeout = timeout

    async def _call_with_retry(self, coro_factory, retryable):
        for attempt in range(self.max_retry):
            try:
                return await coro_factory()
            except TelegramRetryAfter as e:
                logger.warning('RetryAfter, sleeping %s s', e.retry_after)
                await asyncio.sleep(e.retry_after)
            except TelegramNetworkError as e:
                if attempt == self.max_retry - 1:
                    raise
                logger.warning('Network error (%s), retry %s/%s',
                                e, attempt + 1, self.max_retry)
                await asyncio.sleep(self.timeout * (attempt + 1))
            except MessageNotModified:
                raise
        raise RuntimeError('Unreachable')

    async def edit_message(
            self, bot: Bot, new_message: NewMessage, old_message: OldMessage,
    ) -> Message:
        async def call():
            return await MessageManager.edit_message(
                self, bot, new_message, old_message,
            )
        return await self._call_with_retry(call, retryable=True)
