from aiogram import Router, types
from aiogram.filters import Command

from services.notification_service import NotificationService
from utils.decorators import onboarding_required

router = Router()
notification_service = NotificationService()


@router.message(Command(commands=["notify", "notificacion"]))
@onboarding_required
async def create_notification(message: types.Message, user):
    await notification_service.create_notification(
        user_id=user.telegram_id,
        notification_type="manual",
        message="Lo has logrado... probablemente por accidente.",
        tone="sarcastic",
        character="Lucien",
    )
    await message.answer("🔔 Notificación programada")
