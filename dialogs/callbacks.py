from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery

from dialogs import states



async def select_collection(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(state=states.Select_collection_SG.select)