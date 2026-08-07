from aiogram_dialog import DialogManager
from aiogram.types import User
from aiogram import html
from fluentogram import TranslatorRunner
from aiogram.enums import ContentType
from aiogram_dialog.api.entities import MediaAttachment
from aiogram.enums import ContentType


async def start_hi(dialog_manager: DialogManager,
                    i18n: TranslatorRunner,
                    **kwargs):
    photo = MediaAttachment(type=ContentType.PHOTO, path='data/images/castelia_start_photo.jpg')

    return {'start_bot': i18n.start.bot(),
            'button_start': i18n.button.start()}