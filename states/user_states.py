from aiogram.fsm.state import StatesGroup, State

class UserOnboarding(StatesGroup):
    onboarding = State()

class ViewingBackpack(StatesGroup):
    viewing = State()


class CombiningPieces(StatesGroup):
    combining_pieces = State()


class AwaitingVIPValidation(StatesGroup):
    awaiting_vip_validation = State()
