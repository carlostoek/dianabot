from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from services.analytics_service import AnalyticsService

class AnalyticsMiddleware(BaseMiddleware):
    def __init__(self):
        self.analytics_service = AnalyticsService()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("user")
        
        if isinstance(event, Message):
            await self.analytics_service.track_message(user.id, event.text)
        elif isinstance(event, CallbackQuery):
            await self.analytics_service.track_callback(user.id, event.data)
        
        return await handler(event, data)
