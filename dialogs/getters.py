from aiogram_dialog import DialogManager
from aiogram.types import User
from aiogram import html
from fluentogram import TranslatorRunner
from aiogram.enums import ContentType

async def start_hi(dialog_manager: DialogManager,
                    i18n: TranslatorRunner,
                    **kwargs):
    return {'start_bot': i18n.start.bot}