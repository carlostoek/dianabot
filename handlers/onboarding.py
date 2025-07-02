from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from services.user_service import UserService
from states.user_states import UserOnboarding

router = Router()
user_service = UserService()

WELCOME_TEXT = (
    "🍹 Bienvenido, {first_name}. Soy el Mayordomo.\n"
    "Oh, un usuario más... acompáñame, supongo.\n"
    "Pulsa el botón para 'Abrir mi 👜 colección miserable'"
)

@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext) -> None:
    user = await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
    )
    await message.answer(WELCOME_TEXT.format(first_name=user.first_name))
    await state.set_state(UserOnboarding.onboarding)

@router.message(UserOnboarding.onboarding)
async def finish_onboarding(message: types.Message, state: FSMContext) -> None:
    user = await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
    )
    await user_service.mark_onboarded(user.id)
    await state.clear()
    await message.answer("Onboarding completado. Usa /mochila para ver tus piezas")
