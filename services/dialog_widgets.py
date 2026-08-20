import asyncio
import logging

import aiohttp

from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog import DialogManager
from fluentogram import TranslatorRunner

from dialogs import states
from services import image_api
from database import requests
from database.db import async_session
from services.layouts import LAYOUTS


logger = logging.getLogger(__name__)


async def download_url(url: str, path: str, headers: dict | None = None):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as resp:
            resp.raise_for_status()
            data = await resp.read()
    with open(path, 'wb') as f:
        f.write(data)


async def send_visualization(bot, chat_id, room_path, material_path, user_id, bg, try_another, leave_request, state, size_tile, type_layout):
    photo_layout=LAYOUTS[type_layout]['photo']
    layout_prompt=LAYOUTS[type_layout]['prompt']
    try:
        url, error = await image_api.visualize(room_path, material_path, size_tile, photo_layout, layout_prompt)
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
        await download_url(url, result_path, headers=image_api.API_HEADERS) # pyright: ignore[reportArgumentType]
    except Exception:
        result_path = None
        logger.exception('Не удалось скачать результат визуализации')

    try:
        await state.update_data(result_url=url, result_path=result_path)
    except Exception:
        logger.exception('Не удалось сохранить результат в FSM data')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=try_another, callback_data='try_another')],
        [InlineKeyboardButton(text=leave_request, callback_data='leave_request')]
    ])
    try:
        if result_path:
            await bot.send_photo(chat_id, FSInputFile(result_path), reply_markup=keyboard)
        else:
            await bot.send_photo(chat_id, url, reply_markup=keyboard)
    except Exception:
        logger.exception('Не удалось отправить результат визуализации')
        await bot.send_message(chat_id, 'Не получилось показать результат. Попробуй ещё раз')

    try:
        await bg.done()
    except Exception:
        logger.exception('Не удалось закрыть диалог после визуализации')



async def save_photo(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    i18n = dialog_manager.middleware_data['i18n']

    user_id = message.from_user.id  # type: ignore
    photo = message.photo[-1]  # type: ignore
    path_user = f'data/uploads/{user_id}.jpg'
    await message.bot.download(photo, destination=path_user) # type: ignore

    color_id = dialog_manager.start_data.get('color_id') # type: ignore
    if color_id is None:
        await message.answer(i18n.stop.choice.material())
        return

    async with async_session() as session:
        path_mat = await requests.get_photo_by_color_id(session, int(color_id))
        material_name, color_name = await requests.get_material_and_variant_names(session, int(color_id)) # type: ignore

    size_tile=dialog_manager.start_data.get('size_tile')
    type_layout=dialog_manager.start_data.get('type_layout')

    state = dialog_manager.middleware_data['state']
    await state.update_data(material_id=dialog_manager.start_data.get('material_id'), color_id=color_id, material_name=material_name, \
                            color_name=color_name, user_photo_path=path_user, username=message.from_user.username, size_tile=size_tile,\
                            type_layout=type_layout)

    bg = dialog_manager.bg(user_id=user_id, chat_id=message.chat.id)
    asyncio.create_task(send_visualization(message.bot, message.chat.id, path_user, path_mat, user_id, bg, i18n.to.choice.material(), i18n.leave.request(), state, size_tile, type_layout))

    await dialog_manager.switch_to(state=states.Photo_visualization.processing_visualization)