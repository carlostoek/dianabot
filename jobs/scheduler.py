from celery import Celery
from celery.schedules import crontab
from services.user_service import UserService
from services.mission_service import MissionService
from services.auction_service import AuctionService
from services.channel_service import ChannelService
from datetime import datetime, timedelta
import logging

# Configurar Celery
celery_app = Celery("diana_bot")
celery_app.conf.update(
    broker_url="redis://localhost:6379/0",
    result_backend="redis://localhost:6379/0",
    timezone="UTC",
    beat_schedule={
        "generate-daily-missions": {
            "task": "jobs.scheduler.generate_daily_missions",
            "schedule": crontab(hour=0, minute=0),  # Medianoche
        },
        "process-auction-endings": {
            "task": "jobs.scheduler.process_auction_endings",
            "schedule": crontab(minute="*/5"),  # Cada 5 minutos
        },
        "auto-approve-channels": {
            "task": "jobs.scheduler.auto_approve_channel_requests",
            "schedule": crontab(minute="*/10"),  # Cada 10 minutos
        },
        "update-user-levels": {
            "task": "jobs.scheduler.update_user_progression",
            "schedule": crontab(hour="*/2"),  # Cada 2 horas
        },
    },
)


@celery_app.task
def generate_daily_missions():
    """Genera misiones diarias para todos los usuarios activos"""
    try:
        mission_service = MissionService()
        result = mission_service.generate_daily_missions_for_all_users()
        logging.info(f"Misiones diarias generadas: {result['missions_created']}")
        return result
    except Exception as e:
        logging.error(f"Error generando misiones diarias: {e}")
        return {"error": str(e)}


@celery_app.task
def process_auction_endings():
    """Procesa subastas que han terminado"""
    try:
        auction_service = AuctionService()
        result = auction_service.process_ended_auctions()
        logging.info(f"Subastas procesadas: {result['processed_count']}")
        return result
    except Exception as e:
        logging.error(f"Error procesando subastas: {e}")
        return {"error": str(e)}


@celery_app.task
def auto_approve_channel_requests():
    """Auto-aprueba solicitudes de canal según configuración"""
    try:
        channel_service = ChannelService()
        result = channel_service.process_auto_approvals()
        logging.info(f"Solicitudes auto-aprobadas: {result['approved_count']}")
        return result
    except Exception as e:
        logging.error(f"Error en auto-aprobación: {e}")
        return {"error": str(e)}


@celery_app.task
def update_user_progression():
    """Actualiza progresión narrativa de usuarios"""
    try:
        user_service = UserService()
        result = user_service.update_all_user_progressions()
        logging.info(f"Usuarios actualizados: {result['updated_count']}")
        return result
    except Exception as e:
        logging.error(f"Error actualizando progresión: {e}")
        return {"error": str(e)}
   