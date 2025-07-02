from sqlalchemy import select

from database_init import get_session
from models.narrative import UserBackpack, LorePiece

class BackpackService:
    async def get_backpack(self, user_id: int) -> list[LorePiece]:
        async for session in get_session():
            stmt = (
                select(UserBackpack, LorePiece)
                .join(LorePiece, UserBackpack.lore_piece_id == LorePiece.id)
                .where(UserBackpack.user_id == user_id)
            )
            result = await session.execute(stmt)
            items = [lp for _, lp in result.fetchall()]
            return items
