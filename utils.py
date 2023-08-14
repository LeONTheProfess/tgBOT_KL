from aiogram.dispatcher.filters.state import State, StatesGroup


class ClientStates(StatesGroup):
    CHOOSE_FIRST_DATE = State()
    CHOOSE_SECOND_DATE = State()

class Reports:
    BILLING = 'Биллинг'