from aiogram.fsm.state import State, StatesGroup


class StartSG(StatesGroup):
    start = State()

class Select_collection_SG(StatesGroup):
    select_material = State()
    select_view_color = State()
    select_color_with_photo = State()

class Photo_visualization(StatesGroup):
    get_user_photo = State()
    processing_visualization = State()
    result = State()
