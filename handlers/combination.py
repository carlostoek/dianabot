from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from services.combination_service import CombinationService
from utils.decorators import onboarding_required
from states.user_states import CombiningPieces

router = Router()
combination_service = CombinationService()

WELCOME_TEXT = (
    "Envía los dos 🔑 códigos de las piezas a combinar.\n"
    "Pulsa 'Intentar combinar estas 🧹 piezas rotas' cuando estés listo."
)

@router.message(commands=["combinar", "combine"])
@onboarding_required
async def start_combination(message: types.Message, state: FSMContext, user):
    await message.answer(WELCOME_TEXT)
    await state.set_state(CombiningPieces.combining_pieces)

@router.message(CombiningPieces.combining_pieces)
@onboarding_required
async def process_combination(message: types.Message, state: FSMContext, user):
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Necesito dos códigos separados por espacio.")
        return
    result_piece = await combination_service.combine(user.id, parts[0], parts[1])
    await state.clear()
    if result_piece:
        await message.answer(
            f"Esa combinación... fascinante... mente inútil.\nObtienes {result_piece.title}"
        )
    else:
        await message.answer("Nada ocurrió. Tus piezas siguen tan inútiles como antes.")
