import asyncio
import logging
import os
import aiohttp

from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog import DialogManager
from fluentogram import TranslatorRunner

from dialogs import states
from services import image_api
from database import requests
from database.db import async_session


logger = logging.getLogger(__name__)


lead_cache: dict[int, dict] = {}


def remove_file(path: str | None):
    if not path:
        return
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    except OSError:
        logger.exception('Не удалось удалить файл %s', path)


async def download_url(url: str, path: str, headers: dict | None = None):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            resp.raise_for_status()
            data = await resp.read()
    with open(path, 'wb') as f:
        f.write(data)


async def send_visualization(bot, chat_id, room_path, material_path, user_id, bg):
    try:
        url, error = await image_api.visualize(room_path, material_path)
    except Exception:
        logger.exception('Визуализация упала с исключением')
        await bot.send_message(chat_id, 'Не получилось: internal_error. Попробуй ещё раз')
        try:
            await bg.switch_to(states.Photo_visualization.get_user_photo)
        except Exception:
            logger.exception('Не удалось вернуть юзера к загрузке фото')
        return
    if error:
        await bot.send_message(chat_id, f'Не получилось: {error}. Попробуй ещё раз')
        try:
            await bg.switch_to(states.Photo_visualization.get_user_photo)
        except Exception:
            logger.exception('Не удалось вернуть юзера к загрузке фото')
        return

    result_path = f'data/uploads/result_{user_id}.jpg'
    try:
        await download_url(url, result_path, headers=image_api.API_HEADERS)
    except Exception:
        result_path = None
        logger.exception('Не удалось скачать результат визуализации')

    try:
        async with async_session() as session:
            await requests.set_lead_result(session, user_id, result_path, url)
    except Exception:
        logger.exception('Не удалось обновить результат заявки в БД')

    if user_id in lead_cache:
        lead_cache[user_id]['result_path'] = result_path
        lead_cache[user_id]['result_url'] = url

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Примерить другую коллекцию', callback_data='try_another')],
        [InlineKeyboardButton(text='Оставить заявку / Запросить расчёт', callback_data='leave_request')],
    ])
    try:
        await bg.done()
    except Exception:
        logger.exception('Не удалось закрыть диалог после визуализации')
    try:
        if result_path:
            await bot.send_photo(chat_id, FSInputFile(result_path), reply_markup=keyboard)
        else:
            await bot.send_photo(chat_id, url, reply_markup=keyboard)
    except Exception:
        logger.exception('Не удалось отправить результат визуализации')
        await bot.send_message(chat_id, 'Не получилось показать результат. Попробуй ещё раз')


async def save_photo(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    print('DEBUG dialog_data:', dialog_manager.dialog_data)
    i18n = dialog_manager.middleware_data['i18n']

    user_id = message.from_user.id # type: ignore
    photo = message.photo[-1] # type: ignore
    path_user = f'data/uploads/{user_id}.jpg'
    remove_file(lead_cache.get(user_id, {}).get('result_path'))
    await message.bot.download(photo, destination=path_user)

    dialog_manager.dialog_data['user_photo_path'] = path_user
    color_id = dialog_manager.start_data.get('color_id')
    if color_id is None:
        await message.answer(i18n.stop.choice.material())
        return

    async with async_session() as session:
        path_mat = await requests.get_photo_by_color_id(session, int(color_id))
        material_name, color_name = await requests.get_material_and_variant_names(session, int(color_id))

    lead_cache[user_id] = {
        'material_id': dialog_manager.start_data.get('material_id'),
        'color_id': color_id,
        'username': message.from_user.username,
        'user_photo_path': path_user,
        'material_name': material_name,
        'color_name': color_name,
    }

    try:
        async with async_session() as session:
            await requests.add_lead(
                session,
                telegram_id=user_id,
                username=message.from_user.username,
                material_name=material_name,
                color_name=color_name,
                user_photo_path=path_user,
            )
        logger.info('Заявка сохранена в БД: user_id=%s, material=%s, color=%s', user_id, material_name, color_name)
    except Exception:
        logger.exception('Не удалось сохранить заявку в БД для user_id=%s', user_id)

    bg = dialog_manager.bg(user_id=user_id, chat_id=message.chat.id)
    asyncio.create_task(send_visualization(message.bot, message.chat.id, path_user, path_mat, user_id, bg))

    await dialog_manager.switch_to(state=states.Photo_visualization.processing_visualization)
