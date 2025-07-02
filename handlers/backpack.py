from aiogram import Router, types

from services.backpack_service import BackpackService
from utils.decorators import onboarding_required
from utils.helpers import format_backpack

router = Router()
backpack_service = BackpackService()

@router.message(commands=['mochila', 'backpack'])
@onboarding_required
async def show_backpack(message: types.Message, user):
    items = await backpack_service.get_backpack(user.id)
    text = format_backpack(items)
    await message.answer(f"👜 Mochila:\n{text}")
