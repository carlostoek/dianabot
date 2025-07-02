from sqlalchemy import select

from database_init import get_session
from models.narrative import LorePiece, UserBackpack

class CombinationService:
    async def combine(self, user_id: int, piece1_code: str, piece2_code: str):
        async for session in get_session():
            stmt = select(LorePiece).where(LorePiece.code.in_([piece1_code, piece2_code]))
            result = await session.execute(stmt)
            pieces = {lp.code: lp for lp in result.scalars().all()}
            piece1 = pieces.get(piece1_code)
            piece2 = pieces.get(piece2_code)
            if not piece1 or not piece2:
                return None
            if piece1.combinable_with != piece2.code or piece2.combinable_with != piece1.code:
                return None
            result_code = piece1.combination_result or piece2.combination_result
            if not result_code:
                return None
            res_stmt = select(LorePiece).where(LorePiece.code == result_code)
            res_result = await session.execute(res_stmt)
            combo_piece = res_result.scalar_one_or_none()
            if not combo_piece:
                return None
            check_stmt = select(UserBackpack).where(
                UserBackpack.user_id == user_id,
                UserBackpack.lore_piece_id == combo_piece.id,
            )
            check_res = await session.execute(check_stmt)
            if check_res.scalar_one_or_none() is None:
                session.add(UserBackpack(user_id=user_id, lore_piece_id=combo_piece.id))
                await session.commit()
            return combo_piece
