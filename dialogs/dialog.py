from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Format, Const

from dialogs import getters, states


start_dialog = Dialog(
    Window(Format('start_hi'),
        getter=getters.start_hi,
        state=states.StartSG.start)
)