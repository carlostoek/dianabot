"""Scheduled jobs for periodic tasks."""

from services.mission_service import MissionService
from services.channel_service import ChannelService
from services.notification_service import NotificationService


def generate_daily_missions_for_all_users():
    """Generate daily missions for every registered user."""

    mission_service = MissionService()
    users = mission_service.get_all_users()

    for user in users:
        mission_service.create_daily_missions_for_user(user.id)


def process_auction_endings():
    print("Procesando fin de subastas (placeholder)")


def auto_approve_channel_requests():
    """Approve all pending join requests in every channel."""

    channel_service = ChannelService()
    channels = channel_service.get_all_channels()

    for channel in channels:
        channel_service.approve_pending_requests(channel.id)


def update_user_progression():
    print("Actualizando progresión de usuarios (placeholder)")


def check_vip_expiring():
    """Notify users whose VIP status is about to expire."""

    notification_service = NotificationService()
    users = notification_service.get_all_vip_users()

    for user in users:
        if user.vip_expires_soon():
            notification_service.notify_vip_status(
                user.id, "expiring", {"days_left": user.days_left()}
            )
