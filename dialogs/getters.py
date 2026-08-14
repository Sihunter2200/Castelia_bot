from aiogram_dialog import DialogManager
from aiogram.types import User
from aiogram import html
from fluentogram import TranslatorRunner
from aiogram.enums import ContentType
from aiogram_dialog.api.entities import MediaAttachment
from aiogram.enums import ContentType

from database.db import async_session
from database import requests

async def start_hi(dialog_manager: DialogManager,
                    i18n: TranslatorRunner,
                    **kwargs):
    photo = MediaAttachment(type=ContentType.PHOTO, path='data/images/castelia_start_photo.jpg')

    return {'start_bot': i18n.start.bot(),
            'button_start': i18n.button.start(),
            'photo': photo}


async def material_selection(dialog_manager: DialogManager,
                            i18n: TranslatorRunner,
                            **kwargs):
    group = int(dialog_manager.dialog_data.get('group', 1))

    async with async_session() as session:
        materials = await requests.get_material_by_group(session, group)
        menu_photo = await requests.get_photo_by_group(session, group)

    photo = MediaAttachment(
		type=ContentType.PHOTO,
		path=menu_photo or 'data/images/castelia_start_photo.jpg'
	)

    return {'materials': [{'id': m.id, 'name': m.name} for m in materials],
            'photo': photo,
            'collection_select': i18n.collection.select()}


async def select_color_gett(dialog_manager: DialogManager,
                            i18n: TranslatorRunner,
                            **kwargs):

    material_id = dialog_manager.dialog_data.get('material_id') # type: ignore
    if material_id is None:
        return {'choice_color': i18n.choice.color(),
            'name_color': []}
    material_id = int(material_id)

    async with async_session() as session:
        name_color = await requests.get_name_by_id_material(session, material_id)

    return {'choice_color': i18n.choice.color(),
            'name_color': name_color}


async def select_photo_by_color_id(dialog_manager: DialogManager,
                                i18n: TranslatorRunner,
                                **kwargs):
    color_id = int(dialog_manager.dialog_data.get('color_id')) # type: ignore

    async with async_session() as session:
        path = await requests.get_photo_by_color_id(session, color_id)

    photo = MediaAttachment(
        type=ContentType.PHOTO,
        path=path if path else None
    )

    return {'photo': photo,
            'choice_color_itog': i18n.choice.color.itog(),
            'choice_color_back': i18n.choice.color.back()}


async def photo_reception(dialog_manager: DialogManager,
                            i18n: TranslatorRunner,
                            **kwargs):

    return {'waiting_photo': i18n.waiting.photo()}


async def photo_in_process(dialog_manager: DialogManager,
                            i18n: TranslatorRunner,
                            **kwargs):
    return {'process_visual': i18n.process.visual()}