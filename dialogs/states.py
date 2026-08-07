from aiogram.fsm.state import State, StatesGroup


class StartSG(StatesGroup):
    start = State()

class Select_collection_SG(StatesGroup):
    select = State()
