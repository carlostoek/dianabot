from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

class AuthMiddleware(BaseMiddleware):
    def __init__(self):
        pass

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Por ahora solo pasar el evento sin procesamiento adicional
        try:
            return await handler(event, data)
        except Exception as e:
            print(f"Error en middleware: {e}")
            return await handler(event, data)
