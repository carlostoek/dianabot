from aiogram.fsm.state import State, StatesGroup

class UserOnboarding(StatesGroup):
    onboarding = State()

class ViewingBackpack(StatesGroup):
    viewing = State()
