from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, FSInputFile
from aiogram_dialog import DialogManager, StartMode, ShowMode
import logging
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from aiogram.fsm.context import FSMContext

from config_data.config import load_config
from dialogs import states
from database import requests



logger = logging.getLogger(__name__)

user_router = Router()


@user_router.message(CommandStart())
async def start_command(message: Message,
                        dialog_manager: DialogManager,
                        session_maker: async_sessionmaker[AsyncSession]):
    logger.info('Запуск хэндлера команды start')

    async with session_maker() as session:
        await requests.add_user(session, telegram_id=message.from_user.id, username=message.from_user.username)

    await dialog_manager.start(state=states.StartSG.start, mode=StartMode.RESET_STACK)


@user_router.callback_query(F.data == 'try_another')
async def try_another(callback: CallbackQuery, dialog_manager: DialogManager):
    await callback.answer()
    await dialog_manager.start(state=states.Select_collection_SG.select_material, mode=StartMode.RESET_STACK, show_mode=ShowMode.SEND)


@user_router.callback_query(F.data == 'leave_request')
async def leave_request(callback: CallbackQuery, dialog_manager: DialogManager, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    await dialog_manager.start(states.Forming_cards.get_user_phone, data=data, mode=StartMode.RESET_STACK, show_mode=ShowMode.SEND)