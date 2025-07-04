from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from services.user_service import UserService

class AuthMiddleware(BaseMiddleware):
    def __init__(self):
        self.user_service = UserService()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_data = {
            "telegram_id": event.from_user.id,
            "username": event.from_user.username,
            "first_name": event.from_user.first_name,
            "last_name": event.from_user.last_name
        }
        
        user = await self.user_service.get_or_create_user(user_data)
        data["user"] = user
        
        return await handler(event, data)
