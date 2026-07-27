from aiogram.fsm.state import State, StatesGroup


class SuggestCourse(StatesGroup):
    waiting_text = State()


class AdminEdit(StatesGroup):
    price = State()
    open_link = State()
    product_link = State()
    text_field = State()  # какой именно текст/кнопку редактируем — хранится в FSM data["key"]
