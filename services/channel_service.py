from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text
from models.channel import (
    Channel,
    ChannelMembership,
    ChannelAccessToken,
    ChannelMessage,
    ChannelAnalytics,
    ChannelType,
    ChannelStatus,
    AccessTokenStatus,
    MembershipStatus,
)
from models.user import User
from models.narrative_state import UserNarrativeState, NarrativeLevel
from config.database import get_db
from utils.lucien_voice import LucienVoice
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import random
import string
import json
import uuid


class ChannelService:
    """Servicio completo para gestión de canales de Telegram"""

    def __init__(self):
        self.db = next(get_db())
        self.lucien = LucienVoice()

        # Configuración de canales
        self.DEFAULT_SOCIAL_LINKS = {
            "instagram": "https://instagram.com/diana_profile",
            "twitter": "https://twitter.com/diana_profile",
            "tiktok": "https://tiktok.com/@diana_profile",
            "onlyfans": "https://onlyfans.com/diana_profile",
        }

        # Mensajes de bienvenida por tipo de canal
        self.WELCOME_MESSAGES = self._load_welcome_messages()

        # Configuración de auto-moderación
        self.SPAM_KEYWORDS = [
            "spam",
            "promo",
            "telegram.me",
            "t.me",
            "cryptocurrency",
            "bitcoin",
            "invest",
            "money",
        ]

        # Límites y configuraciones
        self.MAX_PENDING_REQUESTS = 100
        self.TOKEN_EXPIRY_HOURS = 24
        self.AUTO_APPROVAL_MAX_DELAY = 180  # 3 horas máximo

    def create_vip_token(self, user_telegram_id: int, token_type: str) -> Dict[str, Any]:
        """Crea un token VIP para un usuario específico"""

        if token_type == "quick":
            expiry = datetime.utcnow() + timedelta(hours=24)
        elif token_type == "weekly":
            expiry = datetime.utcnow() + timedelta(days=7)
        else:
            return {"success": False, "error": "Tipo de token no válido"}

        token = f"VIP-{user_telegram_id}-{int(expiry.timestamp())}"

        return {
            "success": True,
            "token": token,
            "expiry": expiry.isoformat(),
        }

    # ===== GESTIÓN DE CANALES =====

    def create_channel(self, channel_data: Dict[str, Any]) -> Channel:
        """Crea nuevo canal en el sistema"""

        channel = Channel(
            telegram_id=channel_data["telegram_id"],
            name=channel_data["name"],
            description=channel_data.get("description", ""),
            channel_type=ChannelType(channel_data["type"]),
            requires_approval=channel_data.get("requires_approval", True),
            auto_approval_enabled=channel_data.get("auto_approval_enabled", False),
            auto_approval_delay_minutes=channel_data.get("auto_approval_delay", 30),
            min_narrative_level=channel_data.get("min_narrative_level"),
            vip_only=channel_data.get("vip_only", False),
            welcome_message=channel_data.get("welcome_message", ""),
            rules_message=channel_data.get("rules_message", ""),
            social_media_links=channel_data.get(
                "social_links", self.DEFAULT_SOCIAL_LINKS
            ),
            settings=channel_data.get("settings", {}),
        )

        self.db.add(channel)
        self.db.commit()
        self.db.refresh(channel)

        # Configurar mensaje de bienvenida por defecto si no se proporcionó
        if not channel.welcome_message:
            channel.welcome_message = self._get_default_welcome_message(
                channel.channel_type
            )
            self.db.commit()

        return channel

    def get_channel_by_telegram_id(self, telegram_id: int) -> Optional[Channel]:
        """Obtiene canal por ID de Telegram"""
        return self.db.query(Channel).filter(Channel.telegram_id == telegram_id).first()

    def update_channel_settings(
        self, channel_id: int, settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Actualiza configuración del canal"""

        channel = self.db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            return {"error": "Canal no encontrado"}

        # Actualizar campos permitidos
        updatable_fields = [
            "description",
            "requires_approval",
            "auto_approval_enabled",
            "auto_approval_delay_minutes",
            "welcome_message",
            "rules_message",
            "auto_moderation_enabled",
            "spam_detection_enabled",
        ]

        for field in updatable_fields:
            if field in settings:
                setattr(channel, field, settings[field])

        # Actualizar configuraciones específicas
        if "settings" in settings:
            channel.settings = {**channel.settings, **settings["settings"]}

        if "social_links" in settings:
            channel.social_media_links = settings["social_links"]

        channel.updated_at = datetime.utcnow()
        self.db.commit()

        return {"success": True, "message": "Canal actualizado correctamente"}

    # ===== SISTEMA DE ACCESO VIP CON TOKENS =====

    def generate_vip_access_token(
        self, channel_id: int, admin_user_id: int, token_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Genera token de acceso VIP para admin"""

        channel = self.db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            return {"error": "Canal no encontrado"}

        if channel.channel_type != ChannelType.VIP:
            return {"error": "Solo se pueden generar tokens para canales VIP"}

        # Generar token único
        token = self._generate_unique_token()

        # Configurar expiración
        expires_at = datetime.utcnow() + timedelta(
            hours=token_config.get("expiry_hours", self.TOKEN_EXPIRY_HOURS)
        )

        # Crear token de acceso
        access_token = ChannelAccessToken(
            channel_id=channel_id,
            token=token,
            created_by_user_id=admin_user_id,
            max_uses=token_config.get("max_uses", 1),
            expires_at=expires_at,
            description=token_config.get("description", "Token VIP generado por admin"),
            target_user_name=token_config.get("target_user_name", ""),
        )

        self.db.add(access_token)
        self.db.commit()
        self.db.refresh(access_token)

        # Generar link de invitación
        invite_link = f"https://t.me/your_bot?start=vip_token_{token}"

        return {
            "success": True,
            "token": token,
            "invite_link": invite_link,
            "expires_at": expires_at.isoformat(),
            "max_uses": access_token.max_uses,
            "description": access_token.description,
        }

    def validate_and_use_vip_token(self, token: str, user_id: int) -> Dict[str, Any]:
        """Valida y usa token VIP para dar acceso"""

        access_token = (
            self.db.query(ChannelAccessToken)
            .filter(ChannelAccessToken.token == token)
            .first()
        )

        if not access_token:
            return {"error": "Token no válido"}

        # Validaciones del token
        validation_result = self._validate_access_token(access_token, user_id)
        if not validation_result["valid"]:
            return {"error": validation_result["message"]}

        # Obtener canal y usuario
        channel = (
            self.db.query(Channel).filter(Channel.id == access_token.channel_id).first()
        )
        user = self.db.query(User).filter(User.id == user_id).first()

        if not channel or not user:
            return {"error": "Canal o usuario no encontrado"}

        # Verificar si ya es miembro
        existing_membership = (
            self.db.query(ChannelMembership)
            .filter(
                and_(
                    ChannelMembership.channel_id == channel.id,
                    ChannelMembership.user_id == user_id,
                )
            )
            .first()
        )

        if (
            existing_membership
            and existing_membership.status == MembershipStatus.APPROVED
        ):
            return {"error": "Ya eres miembro de este canal"}

        # Crear o actualizar membresía
        if existing_membership:
            existing_membership.status = MembershipStatus.APPROVED
            existing_membership.approved_at = datetime.utcnow()
            existing_membership.joined_via = "token"
            existing_membership.access_token_used = token
            membership = existing_membership
        else:
            membership = ChannelMembership(
                channel_id=channel.id,
                user_id=user_id,
                telegram_user_id=user.telegram_id,
                status=MembershipStatus.APPROVED,
                requested_at=datetime.utcnow(),
                approved_at=datetime.utcnow(),
                joined_via="token",
                access_token_used=token,
                join_metadata={
                    "token_used": token,
                    "admin_granted": True,
                    "instant_access": True,
                },
            )
            self.db.add(membership)

        # Actualizar uso del token
        access_token.current_uses += 1
        if access_token.current_uses >= access_token.max_uses:
            access_token.status = AccessTokenStatus.USED

        # Registrar uso
        usage_log = access_token.usage_log or []
        usage_log.append(
            {
                "user_id": user_id,
                "user_name": user.first_name,
                "used_at": datetime.utcnow().isoformat(),
                "telegram_id": user.telegram_id,
            }
        )
        access_token.usage_log = usage_log

        used_by = access_token.used_by_user_ids or []
        if user_id not in used_by:
            used_by.append(user_id)
            access_token.used_by_user_ids = used_by

        # Actualizar contador de miembros del canal
        channel.total_members += 1

        self.db.commit()

        # Generar mensaje de bienvenida VIP
        welcome_message = self._generate_vip_welcome_message(channel, user, membership)

        return {
            "success": True,
            "channel_name": channel.name,
            "access_granted": True,
            "membership_id": membership.id,
            "welcome_message": welcome_message,
            "channel_telegram_id": channel.telegram_id,
        }

    def get_vip_tokens_for_channel(self, channel_id: int) -> List[Dict[str, Any]]:
        """Obtiene tokens VIP activos para un canal"""

        tokens = (
            self.db.query(ChannelAccessToken)
            .filter(
                and_(
                    ChannelAccessToken.channel_id == channel_id,
                    ChannelAccessToken.status.in_(
                        [AccessTokenStatus.ACTIVE, AccessTokenStatus.USED]
                    ),
                )
            )
            .order_by(desc(ChannelAccessToken.created_at))
            .all()
        )

        tokens_data = []
        for token in tokens:
            tokens_data.append(
                {
                    "id": token.id,
                    "token": token.token,
                    "description": token.description,
                    "target_user": token.target_user_name,
                    "max_uses": token.max_uses,
                    "current_uses": token.current_uses,
                    "status": token.status.value,
                    "expires_at": (
                        token.expires_at.isoformat() if token.expires_at else None
                    ),
                    "created_at": token.created_at.isoformat(),
                    "used_by_count": len(token.used_by_user_ids or []),
                }
            )

        return tokens_data

    # ===== GESTIÓN DE CANAL GRATUITO =====

    def handle_join_request(
        self, channel_telegram_id: int, user_id: int, telegram_user_id: int
    ) -> Dict[str, Any]:
        """Maneja solicitud de ingreso al canal gratuito"""

        channel = self.get_channel_by_telegram_id(channel_telegram_id)
        if not channel:
            return {"error": "Canal no encontrado"}

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado en el sistema"}

        # Verificar si ya tiene solicitud o membresía
        existing_membership = (
            self.db.query(ChannelMembership)
            .filter(
                and_(
                    ChannelMembership.channel_id == channel.id,
                    ChannelMembership.user_id == user_id,
                )
            )
            .first()
        )

        if existing_membership:
            if existing_membership.status == MembershipStatus.APPROVED:
                return {"error": "Ya eres miembro de este canal"}
            elif existing_membership.status == MembershipStatus.PENDING:
                return {"error": "Ya tienes una solicitud pendiente"}
            elif existing_membership.status == MembershipStatus.BANNED:
                return {"error": "Tu acceso a este canal ha sido restringido"}

        # Crear nueva solicitud de membresía
        membership = ChannelMembership(
            channel_id=channel.id,
            user_id=user_id,
            telegram_user_id=telegram_user_id,
            status=MembershipStatus.PENDING,
            joined_via="public_request",
            join_metadata={
                "source": "social_media",
                "auto_message_sent": True,
                "request_timestamp": datetime.utcnow().isoformat(),
            },
        )

        self.db.add(membership)

        # Actualizar contador de solicitudes pendientes
        channel.pending_requests += 1

        self.db.commit()
        self.db.refresh(membership)

        # Generar mensaje automático de solicitud
        auto_message = self._generate_join_request_auto_message(
            channel, user, membership
        )

        # Programar auto-aprobación si está habilitada
        auto_approval_info = None
        if channel.auto_approval_enabled and channel.auto_approval_delay_minutes > 0:
            auto_approval_time = datetime.utcnow() + timedelta(
                minutes=channel.auto_approval_delay_minutes
            )
            auto_approval_info = {
                "enabled": True,
                "scheduled_for": auto_approval_time.isoformat(),
                "delay_minutes": channel.auto_approval_delay_minutes,
            }

            # Aquí se programaría la tarea de auto-aprobación (implementar con Celery)
            self._schedule_auto_approval(membership.id, auto_approval_time)

        return {
            "success": True,
            "membership_id": membership.id,
            "status": "pending",
            "auto_message": auto_message,
            "auto_approval": auto_approval_info,
            "channel_name": channel.name,
        }

    def approve_join_request(
        self,
        membership_id: int,
        admin_user_id: Optional[int] = None,
        auto_approved: bool = False,
    ) -> Dict[str, Any]:
        """Aprueba solicitud de ingreso"""

        membership = (
            self.db.query(ChannelMembership)
            .filter(ChannelMembership.id == membership_id)
            .first()
        )

        if not membership:
            return {"error": "Solicitud no encontrada"}

        if membership.status != MembershipStatus.PENDING:
            return {"error": "La solicitud no está pendiente"}

        # Aprobar membresía
        membership.status = MembershipStatus.APPROVED
        membership.approved_at = datetime.utcnow()
        membership.approved_by_user_id = admin_user_id

        if auto_approved:
            membership.join_metadata["auto_approved"] = True
            membership.join_metadata["approval_type"] = "automatic"
        else:
            membership.join_metadata["approval_type"] = "manual"
            membership.join_metadata["approved_by_admin"] = admin_user_id

        # Actualizar contadores del canal
        channel = (
            self.db.query(Channel).filter(Channel.id == membership.channel_id).first()
        )
        channel.total_members += 1
        channel.pending_requests = max(0, channel.pending_requests - 1)

        self.db.commit()

        # Generar mensaje de aprobación
        approval_message = self._generate_approval_message(
            channel, membership, auto_approved
        )

        return {
            "success": True,
            "membership_id": membership.id,
            "channel_name": channel.name,
            "channel_telegram_id": channel.telegram_id,
            "user_telegram_id": membership.telegram_user_id,
            "approval_message": approval_message,
            "auto_approved": auto_approved,
        }

    def reject_join_request(
        self, membership_id: int, admin_user_id: int, reason: str = ""
    ) -> Dict[str, Any]:
        """Rechaza solicitud de ingreso"""

        membership = (
            self.db.query(ChannelMembership)
            .filter(ChannelMembership.id == membership_id)
            .first()
        )

        if not membership:
            return {"error": "Solicitud no encontrada"}

        if membership.status != MembershipStatus.PENDING:
            return {"error": "La solicitud no está pendiente"}

        # Rechazar membresía
        membership.status = MembershipStatus.REJECTED
        membership.rejection_reason = reason
        membership.join_metadata["rejected_by_admin"] = admin_user_id
        membership.join_metadata["rejection_timestamp"] = datetime.utcnow().isoformat()

        # Actualizar contador del canal
        channel = (
            self.db.query(Channel).filter(Channel.id == membership.channel_id).first()
        )
        channel.pending_requests = max(0, channel.pending_requests - 1)

        self.db.commit()

        return {
            "success": True,
            "membership_id": membership.id,
            "status": "rejected",
            "reason": reason,
        }

    def get_pending_requests(
        self, channel_id: int, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Obtiene solicitudes pendientes de un canal"""

        pending_memberships = (
            self.db.query(ChannelMembership)
            .filter(
                and_(
                    ChannelMembership.channel_id == channel_id,
                    ChannelMembership.status == MembershipStatus.PENDING,
                )
            )
            .order_by(ChannelMembership.requested_at)
            .limit(limit)
            .all()
        )

        requests_data = []
        for membership in pending_memberships:
            user = self.db.query(User).filter(User.id == membership.user_id).first()

            # Calcular tiempo de espera
            wait_time = datetime.utcnow() - membership.requested_at

            requests_data.append(
                {
                    "membership_id": membership.id,
                    "user_name": user.first_name if user else "Usuario desconocido",
                    "telegram_user_id": membership.telegram_user_id,
                    "requested_at": membership.requested_at.isoformat(),
                    "wait_time_minutes": int(wait_time.total_seconds() / 60),
                    "join_metadata": membership.join_metadata,
                }
            )

        return requests_data

    # ===== ACCESO AUTOMÁTICO POR PROGRESO NARRATIVO =====

    def check_automatic_vip_access(self, user_id: int) -> Dict[str, Any]:
        """Verifica y otorga acceso VIP automático por progreso narrativo"""

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "Usuario no encontrado"}

        from services.user_service import UserService

        user_service = UserService()
        narrative_state = user_service.get_or_create_narrative_state(user_id)

        # Verificar si califica para acceso al Diván
        qualifies_for_divan = (
            narrative_state.has_divan_access
            or narrative_state.current_level
            in [
                NarrativeLevel.LEVEL_4_DIVAN_ENTRY,
                NarrativeLevel.LEVEL_5_DIVAN_DEEP,
                NarrativeLevel.LEVEL_6_DIVAN_SUPREME,
            ]
        )

        if not qualifies_for_divan:
            return {
                "qualifies": False,
                "current_level": narrative_state.current_level.value,
                "required_level": "LEVEL_4_DIVAN_ENTRY",
                "message": "Progreso narrativo insuficiente para acceso VIP automático",
            }

        # Buscar canal VIP
        vip_channel = (
            self.db.query(Channel)
            .filter(Channel.channel_type == ChannelType.VIP)
            .first()
        )

        if not vip_channel:
            return {"error": "Canal VIP no configurado"}

        # Verificar si ya tiene membresía
        existing_membership = (
            self.db.query(ChannelMembership)
            .filter(
                and_(
                    ChannelMembership.channel_id == vip_channel.id,
                    ChannelMembership.user_id == user_id,
                    ChannelMembership.status == MembershipStatus.APPROVED,
                )
            )
            .first()
        )

        if existing_membership:
            return {
                "qualifies": True,
                "already_member": True,
                "message": "Ya tienes acceso al canal VIP",
            }

        # Crear membresía automática
        membership = ChannelMembership(
            channel_id=vip_channel.id,
            user_id=user_id,
            telegram_user_id=user.telegram_id,
            status=MembershipStatus.APPROVED,
            requested_at=datetime.utcnow(),
            approved_at=datetime.utcnow(),
            joined_via="automatic_narrative",
            join_metadata={
                "automatic_access": True,
                "narrative_level": narrative_state.current_level.value,
                "diana_trust_level": narrative_state.diana_trust_level,
                "auto_granted_timestamp": datetime.utcnow().isoformat(),
            },
        )

        self.db.add(membership)

        # Actualizar contador del canal
        vip_channel.total_members += 1

        self.db.commit()
        self.db.refresh(membership)

        # Generar mensaje de bienvenida especial
        welcome_message = self._generate_automatic_vip_welcome_message(
            vip_channel, user, narrative_state
        )

        return {
            "qualifies": True,
            "access_granted": True,
            "membership_id": membership.id,
            "channel_name": vip_channel.name,
            "channel_telegram_id": vip_channel.telegram_id,
            "welcome_message": welcome_message,
            "narrative_level": narrative_state.current_level.value,
        }

    # ===== MODERACIÓN Y ANALYTICS =====

    def log_channel_message(
        self, channel_telegram_id: int, message_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Registra mensaje del canal para análisis"""

        channel = self.get_channel_by_telegram_id(channel_telegram_id)
        if not channel:
            return {"error": "Canal no encontrado"}

        # Crear registro del mensaje
        message = ChannelMessage(
            channel_id=channel.id,
            user_id=message_data.get("user_id"),
            telegram_message_id=message_data["telegram_message_id"],
            telegram_user_id=message_data["telegram_user_id"],
            message_type=message_data.get("message_type", "text"),
            content=message_data.get("content", ""),
            media_url=message_data.get("media_url"),
            word_count=len(message_data.get("content", "").split()),
            contains_links="http" in message_data.get("content", "").lower(),
            contains_media=message_data.get("message_type") != "text",
            message_metadata=message_data.get("metadata", {}),
        )

        # Análisis automático de spam
        if channel.spam_detection_enabled:
            spam_analysis = self._analyze_message_for_spam(
                message_data.get("content", "")
            )
            message.is_spam = spam_analysis["is_spam"]
            message.spam_score = spam_analysis["score"]

        # Análisis de sentimiento básico
        sentiment_score = self._analyze_message_sentiment(
            message_data.get("content", "")
        )
        message.sentiment_score = sentiment_score

        self.db.add(message)

        # Actualizar contador diario del canal
        channel.daily_messages += 1

        # Actualizar actividad del usuario
        membership = (
            self.db.query(ChannelMembership)
            .filter(
                and_(
                    ChannelMembership.channel_id == channel.id,
                    ChannelMembership.telegram_user_id
                    == message_data["telegram_user_id"],
                )
            )
            .first()
        )

        if membership:
            membership.last_activity_at = datetime.utcnow()
            membership.total_messages += 1

            if not membership.first_message_at:
                membership.first_message_at = datetime.utcnow()

        self.db.commit()

        # Verificar si requiere moderación
        moderation_result = None
        if message.is_spam or message.spam_score > 70:
            moderation_result = self._handle_spam_message(message, channel)

        return {
            "success": True,
            "message_id": message.id,
            "spam_detected": message.is_spam,
            "spam_score": message.spam_score,
            "moderation_action": moderation_result,
        }

    def get_channel_analytics(self, channel_id: int, days: int = 30) -> Dict[str, Any]:
        """Obtiene analytics del canal"""

        since_date = datetime.utcnow() - timedelta(days=days)

        channel = self.db.query(Channel).filter(Channel.id == channel_id).first()
        if not channel:
            return {"error": "Canal no encontrado"}

        # Métricas de membresía
        total_members = (
            self.db.query(ChannelMembership)
            .filter(
                and_(
                    ChannelMembership.channel_id == channel_id,
                    ChannelMembership.status == MembershipStatus.APPROVED,
                )
            )
            .count()
        )

        new_members = (
            self.db.query(ChannelMembership)
            .filter(
                and_(
                    ChannelMembership.channel_id == channel_id,
                    ChannelMembership.approved_at >= since_date,
                    ChannelMembership.status == MembershipStatus.APPROVED,
                )
            )
            .count()
        )

        pending_members = (
            self.db.query(ChannelMembership)
            .filter(
                and_(
                    ChannelMembership.channel_id == channel_id,
                    ChannelMembership.status == MembershipStatus.PENDING,
                )
            )
            .count()
        )

        # Métricas de actividad
        total_messages = (
            self.db.query(ChannelMessage)
            .filter(
                and_(
                    ChannelMessage.channel_id == channel_id,
                    ChannelMessage.sent_at >= since_date,
                )
            )
            .count()
        )

        active_users = (
            self.db.query(func.count(func.distinct(ChannelMessage.user_id)))
            .filter(
                and_(
                    ChannelMessage.channel_id == channel_id,
                    ChannelMessage.sent_at >= since_date,
                )
            )
            .scalar()
            or 0
        )

        # Métricas de moderación
        spam_messages = (
            self.db.query(ChannelMessage)
            .filter(
                and_(
                    ChannelMessage.channel_id == channel_id,
                    ChannelMessage.sent_at >= since_date,
                    ChannelMessage.is_spam == True,
                )
            )
            .count()
        )

        # Top usuarios activos
        top_users = (
            self.db.query(
                ChannelMembership.user_id,
                func.count(ChannelMessage.id).label("message_count"),
            )
            .join(ChannelMessage, ChannelMembership.user_id == ChannelMessage.user_id)
            .filter(
                and_(
                    ChannelMembership.channel_id == channel_id,
                    ChannelMessage.sent_at >= since_date,
                )
            )
            .group_by(ChannelMembership.user_id)
            .order_by(desc("message_count"))
            .limit(10)
            .all()
        )

        return {
            "channel_name": channel.name,
            "channel_type": channel.channel_type.value,
            "period_days": days,
            "membership_metrics": {
                "total_members": total_members,
                "new_members": new_members,
                "pending_requests": pending_members,
                "growth_rate": (new_members / max(total_members - new_members, 1))
                * 100,
            },
            "activity_metrics": {
                "total_messages": total_messages,
                "active_users": active_users,
                "avg_messages_per_user": total_messages / max(active_users, 1),
                "avg_messages_per_day": total_messages / days,
            },
            "moderation_metrics": {
                "spam_messages": spam_messages,
                "spam_rate": (spam_messages / max(total_messages, 1)) * 100,
            },
            "top_users": [
                {"user_id": user_id, "message_count": count}
                for user_id, count in top_users
            ],
        }

    # ===== MÉTODOS AUXILIARES =====

    def _generate_unique_token(self) -> str:
        """Genera token único para acceso"""
        timestamp = str(int(datetime.utcnow().timestamp()))
        random_part = "".join(random.choices(string.ascii_letters + string.digits, k=8))
        return f"VIP_{timestamp}_{random_part}"

    def _validate_access_token(
        self, access_token: ChannelAccessToken, user_id: int
    ) -> Dict[str, Any]:
        """Valida token de acceso"""

        if access_token.status != AccessTokenStatus.ACTIVE:
            return {"valid": False, "message": "Token no está activo"}

        if access_token.expires_at and datetime.utcnow() > access_token.expires_at:
            access_token.status = AccessTokenStatus.EXPIRED
            self.db.commit()
            return {"valid": False, "message": "Token expirado"}

        if access_token.current_uses >= access_token.max_uses:
            return {"valid": False, "message": "Token agotado"}

        # Verificar si el usuario ya usó este token
        used_by = access_token.used_by_user_ids or []
        if user_id in used_by:
            return {"valid": False, "message": "Ya has usado este token"}

        return {"valid": True}

    def _get_default_welcome_message(self, channel_type: ChannelType) -> str:
        """Obtiene mensaje de bienvenida por defecto"""
        return self.WELCOME_MESSAGES.get(channel_type.value, "¡Bienvenido al canal!")

    def _load_welcome_messages(self) -> Dict[str, str]:
        """Carga mensajes de bienvenida por tipo de canal"""
        return {
            "free": f"""
{self.lucien.EMOJIS['lucien']} **¡Bienvenido a Los Kinkys!**

*[Con hospitalidad profesional]*

Has sido aceptado en el círculo inicial de Diana. Aquí comenzará tu verdadero viaje de descubrimiento.

**📋 Reglas básicas:**
• Respeta a todos los miembros
• No spam ni promociones
• Mantén las conversaciones relevantes
• Sigue a Diana en redes sociales para contenido exclusivo

**🔗 Síguenos en:**
• Instagram: @diana_profile
• Twitter: @diana_profile  
• TikTok: @diana_profile

*[Con aire conspiratorio]*
Este es solo el comienzo. Diana observa a quienes demuestran verdadera dedicación...
            """.strip(),
            "vip": f"""
{self.lucien.EMOJIS['diana']} **¡Bienvenido al Diván de Diana!**

*[Diana aparece con una sonrisa exclusiva]*

"*Has demostrado ser especial. Este espacio íntimo es para quienes han ganado mi confianza. Aquí compartimos secretos que otros nunca conocerán...*"

{self.lucien.EMOJIS['lucien']} *[Lucien con reverencia]*

Este es el santuario íntimo de Diana. Solo los más devotos y dignos de confianza tienen acceso.

**✨ Privilegios del Diván:**
• Contenido exclusivo de Diana
• Acceso a subastas premium
• Interacción directa privilegiada
• Eventos especiales solo para miembros

*[Con elegancia]*
Bienvenido al círculo íntimo. Diana está... complacida.
            """.strip(),
        }

    # Continúo con más métodos auxiliares...

    def get_pending_auto_approvals(self) -> List[ChannelMembership]:
        """Return memberships eligible for automatic approval."""

        now = datetime.utcnow()

        pending = (
            self.db.query(ChannelMembership)
            .join(Channel, ChannelMembership.channel_id == Channel.id)
            .filter(
                ChannelMembership.status == MembershipStatus.PENDING,
                Channel.auto_approval_enabled == True,
            )
            .all()
        )

        approvable = []
        for membership in pending:
            delay = membership.channel.auto_approval_delay_minutes or 0
            if membership.requested_at + timedelta(minutes=delay) <= now:
                approvable.append(membership)

        return approvable
   