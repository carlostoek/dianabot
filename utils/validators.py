from aiogram import types

from services.user_service import UserService

user_service = UserService()

async def ensure_user(message: types.Message) -> 'User':
    user = await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
    )
    return user
