import asyncio
from aiogram import Bot

from services.notification_service import NotificationService


class NotificationScheduler:
    def __init__(self, bot: Bot, interval: int = 60):
        self.bot = bot
        self.interval = interval
        self.service = NotificationService()
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def _run(self) -> None:
        while True:
            await self.dispatch_notifications()
            await asyncio.sleep(self.interval)

    async def dispatch_notifications(self) -> None:
        notifications = await self.service.get_pending_notifications()
        for notification in notifications:
            try:
                await self.bot.send_message(notification.user_id, notification.message)
                await self.service.mark_delivered(notification.id)
            except Exception:
                continue
