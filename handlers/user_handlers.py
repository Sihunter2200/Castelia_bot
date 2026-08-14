from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, FSInputFile
from aiogram_dialog import DialogManager, StartMode
import logging
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from config_data.config import load_config
from dialogs import states
from database import requests
from services.dialog_widgets import lead_cache, remove_file


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
    await dialog_manager.start(state=states.Select_collection_SG.select_material, mode=StartMode.RESET_STACK)


@user_router.callback_query(F.data == 'leave_request')
async def leave_request(callback: CallbackQuery, dialog_manager: DialogManager):
    await callback.answer()
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text='📱 Отправить номер телефона', request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await callback.message.answer('Поделитесь номером телефона, менеджер свяжется с вами', reply_markup=keyboard)


@user_router.message(F.contact)
async def contact_handler(message: Message, dialog_manager: DialogManager, session_maker: async_sessionmaker[AsyncSession]):
    user_id = message.from_user.id
    data = lead_cache.get(user_id)

    if data is None:
        logger.info('lead_cache пуст для user_id=%s, ищем заявку в БД', user_id)
        try:
            async with session_maker() as session:
                lead = await requests.get_last_lead(session, user_id)
        except Exception:
            logger.exception('Ошибка БД при поиске заявки для user_id=%s', user_id)
            lead = None
        if lead is None:
            logger.warning('Заявка не найдена ни в кэше, ни в БД для user_id=%s', user_id)
            await message.answer('Начните с выбора материала и загрузки фото', reply_markup=ReplyKeyboardRemove())
            return
        logger.info('Заявка из БД: id=%s, material=%s, color=%s', lead.id, lead.material_name, lead.color_name)
        data = {
            'username': lead.username or message.from_user.username or message.from_user.first_name,
            'material_name': lead.material_name or '',
            'color_name': lead.color_name or '',
            'result_path': lead.result_path,
            'result_url': lead.result_url,
        }

    phone = message.contact.phone_number
    username = data.get('username') or message.from_user.username or message.from_user.first_name
    material = data.get('material_name') or ''
    color = data.get('color_name') or ''

    caption = (
        f'🆕 Новая заявка\n'
        f'👤 {username}\n'
        f'📞 {phone}\n'
        f'🎨 {material} / {color}'
    )

    config = load_config()
    photo = data.get('result_path')
    photo_url = data.get('result_url')
    sent = False
    for manager_id in config.tg_bot.superadmin:
        try:
            if photo:
                await message.bot.send_photo(manager_id, photo=FSInputFile(photo), caption=caption)
            elif photo_url:
                await message.bot.send_photo(manager_id, photo=photo_url, caption=caption)
            else:
                await message.bot.send_message(manager_id, caption)
            sent = True
        except Exception:
            logger.exception('Не удалось отправить заявку менеджеру %s', manager_id)
    if not sent:
        await message.answer('Не удалось отправить заявку, попробуйте позже', reply_markup=ReplyKeyboardRemove())
        return

    lead_cache.pop(user_id, None)
    remove_file(data.get('result_path'))
    remove_file(data.get('user_photo_path'))
    await message.answer('Заявка отправлена, менеджер скоро свяжется с вами ✅', reply_markup=ReplyKeyboardRemove())
    await dialog_manager.start(state=states.StartSG.start, mode=StartMode.RESET_STACK)