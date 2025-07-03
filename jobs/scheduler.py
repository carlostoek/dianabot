"""Scheduled background jobs used by the bot."""

from datetime import datetime, timedelta

from models.auction import Auction, AuctionStatus
from services.auction_service import AuctionService
from services.channel_service import ChannelService
from services.mission_service import MissionService
from services.notification_service import NotificationService
from services.user_service import UserService


def generate_daily_missions_for_all_users() -> None:
    """Generate daily missions for every active user."""

    user_service = UserService()
    mission_service = MissionService()

    users = user_service.get_all_users()
    for user in users:
        mission_service.create_daily_missions_for_user(user.id)


def process_auction_endings() -> None:
    """Close auctions that have reached their ending time."""

    auction_service = AuctionService()

    ending_auctions = (
        auction_service.db.query(Auction)
        .filter(
            Auction.status == AuctionStatus.ACTIVE,
            Auction.ends_at <= datetime.utcnow(),
        )
        .all()
    )

    for auction in ending_auctions:
        auction_service.end_auction(auction.id)


def auto_approve_channel_requests() -> None:
    """Automatically approve pending channel requests when the delay has passed."""

    channel_service = ChannelService()

    pending_memberships = channel_service.get_pending_auto_approvals()

    for membership in pending_memberships:
        channel_service.approve_join_request(membership.id, auto_approved=True)


def update_user_progression() -> None:
    """Check progression related tasks for each user."""

    user_service = UserService()
    channel_service = ChannelService()

    users = user_service.get_all_users()
    for user in users:
        channel_service.check_automatic_vip_access(user.id)


def check_vip_expiring() -> None:
    """Notify users when their VIP status is about to expire."""

    notification_service = NotificationService()
    users = notification_service.get_all_vip_users()

    for user in users:
        if user.vip_expires_soon():
            notification_service.notify_vip_status(
                user.id, "expiring", {"days_left": user.days_left_vip()}
            )

