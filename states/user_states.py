from aiogram.fsm.state import StatesGroup, State

class UserOnboarding(StatesGroup):
    onboarding = State()

class ViewingBackpack(StatesGroup):
    viewing = State()
