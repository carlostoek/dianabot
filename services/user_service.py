from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from database_init import async_session
from models.core import User

class UserService:
    def __init__(self):
        self.sessionmaker = async_session

    async def get_or_create_user(self, telegram_id: int, username: str, first_name: str) -> User:
        async with self.sessionmaker() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user is None:
                user = User(telegram_id=telegram_id, username=username, first_name=first_name)
                session.add(user)
                await session.commit()
                await session.refresh(user)
            return user

    async def mark_onboarded(self, user_id: int):
        async with self.sessionmaker() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one()
            user.is_onboarded = True
            await session.commit()
