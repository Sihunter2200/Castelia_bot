from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog import DialogManager, StartMode
from aiogram.types import CallbackQuery

from dialogs import states



async def select_collection(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(state=states.Select_collection_SG.select_material)


async def material_selected(callback: CallbackQuery, button: Button, dialog_manager: DialogManager, material_id: int):
    dialog_manager.dialog_data['material_id'] = material_id

    await dialog_manager.switch_to(states.Select_collection_SG.select_view_color)


async def group_next(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    current_group = int(dialog_manager.dialog_data.get('group', 1))
    dialog_manager.dialog_data['group'] = min(current_group+1, 3)

    await dialog_manager.switch_to(states.Select_collection_SG.select_material)


async def group_prev(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    current_group = int(dialog_manager.dialog_data.get('group', 1))
    dialog_manager.dialog_data['group'] = max(current_group-1, 1)

    await dialog_manager.switch_to(states.Select_collection_SG.select_material)


async def color_selected(callback: CallbackQuery, button: Button, dialog_manager: DialogManager, color_id: int):
    dialog_manager.dialog_data['color_id'] = color_id

    await dialog_manager.switch_to(states.Select_collection_SG.select_color_with_photo)


async def color_itog(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(
        state=states.Photo_visualization.get_user_photo,
        data={
            'material_id': dialog_manager.dialog_data.get('material_id'),
            'color_id': dialog_manager.dialog_data.get('color_id'),
        },
        mode=StartMode.RESET_STACK,
    )


async def color_back(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.start(state=states.Select_collection_SG.select_material)