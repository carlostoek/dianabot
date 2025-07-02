from sqlalchemy import select

from database_init import get_session
from models.notifications import Notification


class NotificationService:
    async def create_notification(
        self,
        user_id: int,
        notification_type: str,
        message: str,
        tone: str,
        character: str,
    ) -> Notification:
        async for session in get_session():
            notification = Notification(
                user_id=user_id,
                notification_type=notification_type,
                message=message,
                tone=tone,
                character=character,
            )
            session.add(notification)
            await session.commit()
            await session.refresh(notification)
            return notification

    async def get_pending_notifications(self) -> list[Notification]:
        async for session in get_session():
            stmt = select(Notification).where(Notification.was_delivered == False)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def mark_delivered(self, notification_id: int) -> None:
        async for session in get_session():
            stmt = select(Notification).where(Notification.id == notification_id)
            result = await session.execute(stmt)
            notification = result.scalar_one_or_none()
            if notification:
                notification.was_delivered = True
                await session.commit()
