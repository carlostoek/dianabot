from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from services.vip_service import VIPService
from utils.decorators import onboarding_required
from states.user_states import AwaitingVIPValidation

router = Router()
vip_service = VIPService()

@router.message(Command("vip"))
@onboarding_required
async def request_vip(message: types.Message, state: FSMContext, user):
    await message.answer("Ingresa tu 🔑 código VIP:")
    await state.set_state(AwaitingVIPValidation.awaiting_vip_validation)

@router.message(AwaitingVIPValidation.awaiting_vip_validation)
@onboarding_required
async def process_vip_token(message: types.Message, state: FSMContext, user):
    token = message.text.strip()
    access = await vip_service.redeem_token(user.id, token, message.chat.id)
    await state.clear()
    if access:
        expires = (
            access.access_expires.strftime("%Y-%m-%d %H:%M")
            if access.access_expires
            else "indefinido"
        )
        await message.answer(f"🍿 Acceso VIP concedido hasta {expires}")
    else:
        await message.answer("Código inválido. Sigue siendo plebeyo.")
