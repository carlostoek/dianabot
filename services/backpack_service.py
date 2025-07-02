from sqlalchemy import select

from database_init import async_session
from models.narrative import UserBackpack, LorePiece

class BackpackService:
    def __init__(self):
        self.sessionmaker = async_session

    async def get_backpack(self, user_id: int):
        async with self.sessionmaker() as session:
            stmt = (
                select(UserBackpack, LorePiece)
                .join(LorePiece, UserBackpack.lore_piece_id == LorePiece.id)
                .where(UserBackpack.user_id == user_id)
            )
            result = await session.execute(stmt)
            items = [lp for _, lp in result.fetchall()]
            return items
