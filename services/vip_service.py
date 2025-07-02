from datetime import datetime, timedelta
from sqlalchemy import select, update

from database_init import get_session
from models.vip import VIPAccess, VIPToken

class VIPService:
    async def redeem_token(
        self, user_id: int, token: str, channel_id: int, duration_minutes: int = 60
    ):
        async for session in get_session():
            stmt = select(VIPToken).where(VIPToken.token == token)
            result = await session.execute(stmt)
            vip_token = result.scalar_one_or_none()
            if (
                vip_token is None
                or (vip_token.expires_at and vip_token.expires_at < datetime.utcnow())
                or vip_token.used_count >= vip_token.max_uses
            ):
                return None
            vip_token.used_count += 1
            expires = datetime.utcnow() + timedelta(minutes=duration_minutes)
            vip_access = VIPAccess(
                user_id=user_id,
                channel_id=channel_id,
                access_expires=expires,
            )
            session.add(vip_access)
            await session.commit()
            await session.refresh(vip_access)
            return vip_access

    async def has_active_access(self, user_id: int, channel_id: int) -> bool:
        async for session in get_session():
            await session.execute(
                update(VIPAccess)
                .where(VIPAccess.access_expires < datetime.utcnow(), VIPAccess.is_active == True)
                .values(is_active=False)
            )
            await session.commit()
            stmt = select(VIPAccess).where(
                VIPAccess.user_id == user_id,
                VIPAccess.channel_id == channel_id,
                VIPAccess.is_active == True,
                VIPAccess.access_expires > datetime.utcnow(),
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None
