from aiogram import BaseMiddleware
from aiogram.types import Message

from services.vip_service import VIPService

class VIPMiddleware(BaseMiddleware):
    def __init__(self, channel_id: int):
        super().__init__()
        self.channel_id = channel_id
        self.vip_service = VIPService()

    async def __call__(self, handler, event: Message, data: dict):
        user_id = event.from_user.id
        has_access = await self.vip_service.has_active_access(user_id, self.channel_id)
        if not has_access:
            await event.answer("🍿 Necesitas acceso VIP. Ingresa tu código con /vip")
            return
        return await handler(event, data)
