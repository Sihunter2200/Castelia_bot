from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.media import DynamicMedia

from dialogs import getters, states
import dialogs.callbacks as callback


start_dialog = Dialog(
    Window(Format('{start_bot}'),
            DynamicMedia('photo'),
            Button(Format('{button_start}'), id='button_start', on_click=callback.select_collection),
        getter=getters.start_hi,
        state=states.StartSG.start)
    )
