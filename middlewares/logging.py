import logging
from aiogram import BaseMiddleware
from aiogram.types import Message


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        logging.info("%s -> %s", event.from_user.id, event.text)
        return await handler(event, data)
