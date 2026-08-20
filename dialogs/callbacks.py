from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog import DialogManager, StartMode
from aiogram.types import CallbackQuery, Message
from aiogram_dialog.widgets.input import MessageInput

from dialogs import states
from config_data.config import load_config
from services.layouts import LAYOUTS


SIZES = {
    'size_big': '3000х1200',
    'size_average': '2400х1200',
    'size_small': '1200х600'
}


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
    await dialog_manager.switch_to(state=states.Select_collection_SG.select_size_tile)


async def save_type_layout_itog(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    dialog_manager.dialog_data['type_layout'] = button.widget_id
    dialog_manager.dialog_data['layout_photo_path'] = LAYOUTS[button.widget_id]['photo']

    await dialog_manager.start(
        state=states.Photo_visualization.get_user_photo,
        data={
            'material_id': dialog_manager.dialog_data.get('material_id'),
            'color_id': dialog_manager.dialog_data.get('color_id'),
            'size_tile': dialog_manager.dialog_data.get('size_tile'),
            'type_layout': dialog_manager.dialog_data.get('type_layout'),
            'layout_photo_path': dialog_manager.dialog_data.get('layout_photo_path')
        },
        mode=StartMode.RESET_STACK,
    )

async def back_to_choice_color(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.switch_to(state=states.Select_collection_SG.select_view_color)


async def save_size_layout(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    dialog_manager.dialog_data['size_tile'] = SIZES[button.widget_id]

    await dialog_manager.switch_to(state=states.Select_collection_SG.select_layout_tile)



async def back_to_material_color(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    await dialog_manager.switch_to(state=states.Select_collection_SG.select_material)


async def phone_received(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    i18n = dialog_manager.middleware_data['i18n']

    data = dialog_manager.start_data
    phone = message.contact.phone_number # type: ignore

    type_layout_none=dialog_manager.start_data.get('type_layout')

    size_tile=dialog_manager.start_data.get('size_tile')
    type_layout=LAYOUTS[type_layout_none]['label']


    card = (
        f'{i18n.card.new()}\n'
        f'{i18n.card.material()}: {data.get("material_name")}\n' # type: ignore
        f'{i18n.card.color()}: {data.get("color_name")}\n' # type: ignore
        f'{i18n.card.phone()}: {phone}\n'
        f'{i18n.card.size.tile()}: {size_tile}\n'
        f'{i18n.card.type.layout()}: {type_layout}\n'
        f'{i18n.card.result()}: {data.get("result_url")}' # type: ignore
    )

    for admin_id in load_config().tg_bot.superadmin:
        await message.bot.send_message(admin_id, card) # type: ignore

    await dialog_manager.done()
