from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, StartMode
import logging

from dialogs import states


logger = logging.getLogger(__name__)

user_router = Router()


@user_router.message(CommandStart())
async def start_command(message: Message,
                        dialog_manager: DialogManager):
    logger.info('Запуск хэндлера команды start')

    await dialog_manager.start(state=states.StartSG.start, mode=StartMode.RESET_STACK)