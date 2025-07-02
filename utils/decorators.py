from functools import wraps
from aiogram import types

from utils.validators import ensure_user


def onboarding_required(handler):
    @wraps(handler)
    async def wrapper(message: types.Message, *args, **kwargs):
        user = await ensure_user(message)
        if not user.is_onboarded:
            await message.answer("Primero realiza el onboarding con /start")
            return
        return await handler(message, user=user, *args, **kwargs)

    return wrapper
