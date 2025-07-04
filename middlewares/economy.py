from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from services.economy_service import EconomyService

class EconomyMiddleware(BaseMiddleware):
    def __init__(self):
        self.economy_service = EconomyService()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("user")
        
        # Track activity for potential rewards
        await self.economy_service.track_activity(user.id, type(event).__name__)
        
        return await handler(event, data)
