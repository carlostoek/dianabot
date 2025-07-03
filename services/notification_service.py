from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from models.notification import (
    Notification,
    HumorMessage,
    NotificationTemplate,
    NotificationType,
    NotificationPriority,
)
from models.narrative import (
    LorePiece,
    UserLorePiece,
    NarrativeProgress,
    LoreCombination,
)
from models.user import User
from models.mission import UserMission, Mission
from models.auction import Auction, AuctionBid
from config.database import get_db
from config.settings import settings
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import random
import asyncio
import telegram
from telegram import Bot


class NotificationService:
    def __init__(self):
        self.db = next(get_db())
        self.bot = None  # Se inicializa externamente

    def set_bot(self, bot: Bot):
        """Establece la instancia del bot de Telegram"""
        self.bot = bot

    def get_all_vip_users(self) -> List[User]:
        """Return all users with active VIP status."""
        return (
            self.db.query(User)
            .filter(User.is_vip == True)
            .all()
        )

    # ===== NOTIFICATION CREATION =====

    def create_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        data: Optional[Dict] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        send_immediately: bool = True,
        scheduled_for: Optional[datetime] = None,
    ) -> Notification:
        """Crea una nueva notificación"""

        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            priority=priority,
            title=title,
            message=message,
            data=data or {},
            send_immediately=send_immediately,
            scheduled_for=scheduled_for,
        )

        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)

        # Enviar inmediatamente si está configurado
        if send_immediately and self.bot:
            asyncio.create_task(self._send_notification(notification))

        return notification

    def create_from_template(
        self,
        user_id: int,
        notification_type: NotificationType,
        template_data: Dict,
        priority: NotificationPriority = None,
    ) -> Notification:
        """Crea notificación desde plantilla"""

        template = (
            self.db.query(NotificationTemplate)
            .filter(NotificationTemplate.notification_type == notification_type)
            .first()
        )

        if not template:
            # Crear notificación básica si no hay plantilla
            return self.create_notification(
                user_id=user_id,
                notification_type=notification_type,
                title="Notificación",
                message="Tienes una nueva notificación",
                data=template_data,
            )

        # Formatear título y mensaje con los datos
        try:
            title = template.title_template.format(**template_data)
            message = template.message_template.format(**template_data)
        except KeyError:
            title = template.title_template
            message = template.message_template

        return self.create_notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            data=template_data,
            priority=priority or template.priority,
        )

    # ===== SPECIFIC NOTIFICATION TYPES =====

    def notify_level_up(
        self, user_id: int, old_level: int, new_level: int, rewards: Dict
    ):
        """Notifica subida de nivel con humor"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        # Mensaje con humor
        humor_msg = self._get_humor_message("level_up", user)

        title = f"🎉 ¡Nivel {new_level} Alcanzado!"
        message = f"""
{humor_msg}

🆙 **Has subido del nivel {old_level} al {new_level}!**

🎁 **Recompensas:**
💋 +{rewards.get('besitos', 0)} besitos
⚡ +{rewards.get('experience', 0)} experiencia

{self._get_level_milestone_message(new_level)}
        """.strip()

        self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.LEVEL_UP,
            title=title,
            message=message,
            data={"old_level": old_level, "new_level": new_level, "rewards": rewards},
            priority=NotificationPriority.HIGH,
        )

        # Notificar progreso narrativo si es relevante
        self._check_narrative_level_unlock(user_id, new_level)

    def notify_lore_unlocked(self, user_id: int, lore_piece: LorePiece):
        """Notifica nueva pieza de lore desbloqueada"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        rarity_emojis = {"common": "📜", "rare": "📋", "epic": "📃", "legendary": "📑"}

        rarity_messages = {
            "common": "¡Has encontrado una nueva pista!",
            "rare": "¡Descubriste algo importante!",
            "epic": "¡Un hallazgo extraordinario!",
            "legendary": "¡DESCUBRIMIENTO LEGENDARIO!",
        }

        emoji = rarity_emojis.get(lore_piece.rarity, "📜")
        rarity_msg = rarity_messages.get(lore_piece.rarity, "¡Nueva pista encontrada!")

        title = f"{emoji} {rarity_msg}"
        message = f"""
🗺️ **Nueva Pieza de Historia Desbloqueada**

**{lore_piece.title}**

_{lore_piece.description}_

🎁 **Recompensas:**
💋 +{lore_piece.reward_besitos} besitos
⚡ +{lore_piece.reward_experience} experiencia

Capítulo: {lore_piece.chapter} | Rareza: {lore_piece.rarity.title()}

¡Ve a tu mochila para leer la historia completa!
        """.strip()

        self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.LORE_UNLOCKED,
            title=title,
            message=message,
            data={
                "lore_piece_id": lore_piece.id,
                "rarity": lore_piece.rarity,
                "chapter": lore_piece.chapter,
            },
            priority=NotificationPriority.HIGH,
        )

        # Actualizar progreso narrativo
        self._update_narrative_progress(user_id)

    def notify_lore_combination(
        self, user_id: int, combination: LoreCombination, result_piece: LorePiece
    ):
        """Notifica combinación exitosa de lore"""

        title = "✨ ¡Combinación Exitosa!"
        message = f"""
🔮 **¡Has combinado pistas exitosamente!**

**{combination.name}**

{combination.description}

🎁 **Nueva historia desbloqueada:**
📖 **{result_piece.title}**

🎁 **Recompensas:**
💋 +{combination.reward_besitos} besitos
⚡ +{combination.reward_experience} experiencia

¡La historia se vuelve más clara! 🌟
        """.strip()

        self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.LORE_COMBINATION,
            title=title,
            message=message,
            data={
                "combination_id": combination.id,
                "result_piece_id": result_piece.id,
                "reward_besitos": combination.reward_besitos,
            },
            priority=NotificationPriority.HIGH,
        )

    def notify_narrative_progress(self, user_id: int, progress: NarrativeProgress):
        """Notifica progreso en la narrativa"""

        if progress.story_completion_percentage % 10 == 0:  # Cada 10% de progreso

            title = f"📖 Progreso Narrativo: {progress.story_completion_percentage}%"
            message = f"""
🗺️ **Tu aventura continúa...**

📊 **Progreso actual:**
• Capítulo actual: {progress.current_chapter}
• Piezas en este capítulo: {progress.pieces_in_current_chapter}
• Total de piezas: {progress.total_pieces_collected}
• Completado: {progress.story_completion_percentage}%

🔍 Piezas secretas encontradas: {progress.secret_pieces_found}
🔗 Combinaciones realizadas: {progress.combinations_made}

{self._get_narrative_milestone_message(progress.story_completion_percentage)}
            """.strip()

            self.create_notification(
                user_id=user_id,
                notification_type=NotificationType.NARRATIVE_PROGRESS,
                title=title,
                message=message,
                data={
                    "completion_percentage": progress.story_completion_percentage,
                    "current_chapter": progress.current_chapter,
                },
            )

    def notify_mission_completed(self, user_id: int, mission: Mission, rewards: Dict):
        """Notifica misión completada"""
        user = self.db.query(User).filter(User.id == user_id).first()
        humor_msg = self._get_humor_message("mission_complete", user)

        mission_emojis = {
            "daily": "📅",
            "weekly": "📊",
            "special": "⭐",
            "narrative": "📖",
        }

        emoji = mission_emojis.get(mission.mission_type.value, "🎯")

        title = f"{emoji} ¡Misión Completada!"
        message = f"""
{humor_msg}

✅ **{mission.title}**

{mission.description}

🎁 **Recompensas obtenidas:**
💋 +{rewards.get('besitos', 0)} besitos
⚡ +{rewards.get('experience', 0)} experiencia
{f"📜 +Nueva pieza de historia" if rewards.get('lore_piece') else ""}

¡Sigue así, aventurero! 🌟
        """.strip()

        self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.MISSION_COMPLETED,
            title=title,
            message=message,
            data={
                "mission_id": mission.id,
                "mission_type": mission.mission_type.value,
                "rewards": rewards,
            },
            priority=NotificationPriority.NORMAL,
        )

    def notify_auction_events(
        self, user_id: int, event_type: str, auction: Auction, data: Dict = None
    ):
        """Notifica eventos de subastas"""

        if event_type == "outbid":
            title = "💸 Te han superado en una subasta"
            message = f"""
😔 **Te han superado en la subasta:**

🏆 **{auction.title}**

💰 Nueva puja más alta: **{data.get('new_bid', 0):,} besitos**
⏰ Tiempo restante: {self._format_time_remaining(auction.ends_at)}

¡Aún puedes pujar de nuevo! 💪
            """.strip()
            notification_type = NotificationType.AUCTION_OUTBID

        elif event_type == "ending":
            title = "⏰ Subasta terminando pronto"
            message = f"""
🚨 **¡Última oportunidad!**

🏆 **{auction.title}**

💰 Puja actual: **{auction.current_price:,} besitos**
⏰ Termina en: {self._format_time_remaining(auction.ends_at)}

{f"🥇 ¡Estás ganando!" if data.get('is_winning') else "💪 ¡Aún puedes pujar!"}
            """.strip()
            notification_type = NotificationType.AUCTION_ENDING

        elif event_type == "won":
            title = "🎉 ¡Has ganado una subasta!"
            message = f"""
🏆 **¡FELICIDADES!**

Has ganado la subasta:
**{auction.title}**

💰 Precio final: **{auction.winning_bid:,} besitos**

🎁 Los premios se entregarán automáticamente.
¡Disfruta tu victoria! 🎊
            """.strip()
            notification_type = NotificationType.AUCTION_WON

        else:
            return

        self.create_notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            data={"auction_id": auction.id, "event_type": event_type, **(data or {})},
            priority=(
                NotificationPriority.HIGH
                if event_type == "won"
                else NotificationPriority.NORMAL
            ),
        )

    def notify_vip_status(self, user_id: int, event_type: str, data: Dict):
        """Notifica cambios en estado VIP"""

        if event_type == "granted":
            title = "👑 ¡Acceso VIP Otorgado!"
            days = data.get("days", 30)
            message = f"""
🎉 **¡Bienvenido al Club VIP!**

👑 Tu acceso VIP ha sido activado por **{days} días**

🌟 **Beneficios desbloqueados:**
• Acceso a canales exclusivos
• Subastas VIP especiales
• Regalos diarios mejorados
• Misiones premium
• Y mucho más...

¡Disfruta tu experiencia premium! ✨
            """.strip()

        elif event_type == "expiring":
            days_left = data.get("days_left", 1)
            title = "⚠️ VIP expirando pronto"
            message = f"""
👑 **Tu acceso VIP expira pronto**

⏰ Tiempo restante: **{days_left} día{'s' if days_left != 1 else ''}**

💡 No olvides participar en subastas para extender tu membresía o ganar una nueva.

¡Gracias por ser parte del club VIP! 🌟
            """.strip()

        else:
            return

        self.create_notification(
            user_id=user_id,
            notification_type=(
                NotificationType.VIP_GRANTED
                if event_type == "granted"
                else NotificationType.VIP_EXPIRING
            ),
            title=title,
            message=message,
            data=data,
            priority=NotificationPriority.HIGH,
        )

    def notify_daily_gift_available(self, user_id: int):
        """Notifica regalo diario disponible"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return

        # Solo notificar si hace más de 20 horas que reclamó
        if user.last_daily_claim:
            time_since = datetime.utcnow() - user.last_daily_claim
            if time_since < timedelta(hours=20):
                return

        humor_msg = self._get_humor_message("daily_gift", user)

        title = "🎁 ¡Regalo diario disponible!"
        message = f"""
{humor_msg}

🎁 **Tu regalo diario te está esperando!**

💋 Reclama tus besitos gratis con /daily

⭐ Nivel actual: {user.level}
👑 Estado: {'VIP' if user.is_vip else 'Normal'}

¡No olvides reclamar tu regalo! 🌟
        """.strip()

        self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.DAILY_GIFT,
            title=title,
            message=message,
            priority=NotificationPriority.LOW,
        )

    def notify_reaction_reward(
        self, user_id: int, besitos_earned: int, post_info: Dict
    ):
        """Notifica recompensa por reacción"""

        title = "❤️ ¡Reacción recompensada!"
        message = f"""
👍 **¡Gracias por tu reacción!**

💋 Has ganado **{besitos_earned} besitos**

📱 Post: {post_info.get('title', 'Post del canal')}
📍 Canal: {post_info.get('channel_name', 'Canal')}

¡Sigue participando para ganar más! 🌟
        """.strip()

        self.create_notification(
            user_id=user_id,
            notification_type=NotificationType.REACTION_REWARD,
            title=title,
            message=message,
            data={"besitos_earned": besitos_earned, "post_info": post_info},
            priority=NotificationPriority.LOW,
        )

    # ===== HUMOR SYSTEM =====

    def _get_humor_message(self, category: str, user: User) -> str:
        """Obtiene mensaje con humor para una categoría"""

        humor_messages = self.db.query(HumorMessage).filter(
            and_(
                HumorMessage.category == category,
                HumorMessage.is_active == True,
                HumorMessage.min_level <= user.level,
            )
        )

        if not user.is_vip:
            humor_messages = humor_messages.filter(HumorMessage.vip_only == False)

        messages = humor_messages.all()

        if not messages:
            return self._get_default_humor_message(category)

        # Seleccionar mensaje basado en peso
        total_weight = sum(msg.weight for msg in messages)
        random_value = random.randint(1, total_weight)

        current_weight = 0
        for message in messages:
            current_weight += message.weight
            if random_value <= current_weight:
                return message.message_template.format(
                    name=user.first_name, level=user.level, besitos=user.besitos
                )

        return messages[0].message_template.format(
            name=user.first_name, level=user.level, besitos=user.besitos
        )

    def _get_default_humor_message(self, category: str) -> str:
        """Mensajes de humor por defecto"""
        defaults = {
            "level_up": [
                "🎉 ¡{name}, has subido de nivel! ¡Eres imparable!",
                "⭐ ¡Nivel up! {name}, cada vez más cerca de la grandeza.",
                "🚀 ¡{name} sigue escalando! ¡El cielo es el límite!",
                "💪 ¡Increíble, {name}! Tu dedicación está dando frutos.",
            ],
            "mission_complete": [
                "✅ ¡Misión cumplida, {name}! Eres todo un profesional.",
                "🎯 ¡Excelente trabajo, {name}! Tu enfoque es admirable.",
                "⭐ ¡{name}, eres una máquina de cumplir misiones!",
                "🏆 ¡Bravo, {name}! Tu perseverancia es inspiradora.",
            ],
            "daily_gift": [
                "🎁 ¡{name}, tu regalo te extraña!",
                "☀️ ¡Buenos días, {name}! Tu regalo diario te saluda.",
                "💝 ¡{name}, alguien especial te dejó un regalo!",
                "🌟 ¡{name}, empecemos el día con tu regalo!",
            ],
        }

        messages = defaults.get(category, ["¡Excelente, {name}!"])
        return random.choice(messages)

    # ===== UTILITY METHODS =====

    def _get_level_milestone_message(self, level: int) -> str:
        """Mensajes especiales para niveles importantes"""
        milestones = {
            5: "🎊 ¡Nivel 5! Ahora puedes acceder a contenido especial.",
            10: "🏅 ¡Nivel 10! Eres oficialmente un veterano.",
            15: "💎 ¡Nivel 15! Tu experiencia es invaluable.",
            20: "👑 ¡Nivel 20! Te acercas a la élite.",
            25: "🌟 ¡Nivel 25! Tu dedicación es legendaria.",
            30: "🏆 ¡Nivel 30! Eres un verdadero maestro.",
            50: "⚡ ¡Nivel 50! Tu poder es inconmensurable.",
            100: "🔥 ¡NIVEL 100! ¡ERES UNA LEYENDA VIVIENTE!",
        }

        if level in milestones:
            return f"\n\n{milestones[level]}"
        elif level % 10 == 0:
            return f"\n\n🎉 ¡Nivel {level}! Cada paso te acerca más a la grandeza."

        return ""

    def _get_narrative_milestone_message(self, percentage: int) -> str:
        """Mensajes para hitos narrativos"""
        milestones = {
            10: "🌱 La aventura apenas comienza...",
            25: "🗺️ Los misterios se van revelando...",
            50: "🔍 Estás en el corazón de la historia...",
            75: "⚡ La verdad está al alcance...",
            90: "🌟 El final se aproxima...",
            100: "👑 ¡Has completado toda la saga! ¡Eres un maestro de los secretos!",
        }

        return milestones.get(percentage, "🔍 La historia continúa...")

    def _format_time_remaining(self, end_time: datetime) -> str:
        """Formatea tiempo restante de manera legible"""
        now = datetime.utcnow()
        if end_time <= now:
            return "¡Ya terminó!"

        diff = end_time - now
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def _check_narrative_level_unlock(self, user_id: int, new_level: int):
        """Verifica si el nuevo nivel desbloquea contenido narrativo"""
        # Buscar piezas de lore que se desbloqueen con este nivel
        unlocked_pieces = (
            self.db.query(LorePiece).filter(LorePiece.required_level == new_level).all()
        )

        for piece in unlocked_pieces:
            # Verificar si el usuario ya tiene esta pieza
            existing = (
                self.db.query(UserLorePiece)
                .filter(
                    and_(
                        UserLorePiece.user_id == user_id,
                        UserLorePiece.lore_piece_id == piece.id,
                    )
                )
                .first()
            )

            if not existing:
                # Dar la pieza automáticamente
                user_piece = UserLorePiece(user_id=user_id, lore_piece_id=piece.id)
                self.db.add(user_piece)
                self.db.commit()

                # Notificar
                self.notify_lore_unlocked(user_id, piece)

    def _update_narrative_progress(self, user_id: int):
        """Actualiza el progreso narrativo de un usuario"""

        # Obtener o crear progreso
        progress = (
            self.db.query(NarrativeProgress)
            .filter(NarrativeProgress.user_id == user_id)
            .first()
        )

        if not progress:
            progress = NarrativeProgress(user_id=user_id)
            self.db.add(progress)

        # Contar piezas del usuario
        user_pieces = (
            self.db.query(UserLorePiece)
            .filter(UserLorePiece.user_id == user_id)
            .count()
        )

        # Contar piezas totales disponibles
        total_pieces = self.db.query(LorePiece).count()

        # Actualizar progreso
        progress.total_pieces_collected = user_pieces
        if total_pieces > 0:
            progress.story_completion_percentage = int(
                (user_pieces / total_pieces) * 100
            )

        # Contar piezas secretas
        secret_pieces = (
            self.db.query(UserLorePiece)
            .join(LorePiece)
            .filter(and_(UserLorePiece.user_id == user_id, LorePiece.is_secret == True))
            .count()
        )
        progress.secret_pieces_found = secret_pieces

        progress.last_updated = datetime.utcnow()
        self.db.commit()

        # Notificar progreso si es significativo
        self.notify_narrative_progress(user_id, progress)

    # ===== NOTIFICATION SENDING =====

    async def _send_notification(self, notification: Notification):
        """Envía notificación por Telegram"""
        if not self.bot:
            return

        try:
            user = self.db.query(User).filter(User.id == notification.user_id).first()
            if not user:
                return

            await self.bot.send_message(
                chat_id=user.telegram_id,
                text=f"**{notification.title}**\n\n{notification.message}",
                parse_mode="Markdown",
            )

            notification.is_sent = True
            notification.sent_at = datetime.utcnow()
            self.db.commit()

        except Exception as e:
            print(f"Error sending notification: {e}")

    async def send_pending_notifications(self):
        """Envía notificaciones pendientes"""
        if not self.bot:
            return

        pending = (
            self.db.query(Notification)
            .filter(
                and_(
                    Notification.is_sent == False,
                    or_(
                        Notification.scheduled_for.is_(None),
                        Notification.scheduled_for <= datetime.utcnow(),
                    ),
                )
            )
            .limit(50)
            .all()
        )  # Procesar en lotes

        for notification in pending:
            await self._send_notification(notification)
            await asyncio.sleep(0.1)  # Evitar spam

    # ===== MANAGEMENT =====

    def get_user_notifications(
        self, user_id: int, unread_only: bool = False, limit: int = 20
    ) -> List[Notification]:
        """Obtiene notificaciones de un usuario"""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)

        if unread_only:
            query = query.filter(Notification.is_read == False)

        return query.order_by(Notification.created_at.desc()).limit(limit).all()

    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """Marca notificación como leída"""
        notification = (
            self.db.query(Notification)
            .filter(
                and_(
                    Notification.id == notification_id, Notification.user_id == user_id
                )
            )
            .first()
        )

        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            self.db.commit()
            return True

        return False

    def cleanup_old_notifications(self, days_old: int = 30):
        """Limpia notificaciones antiguas"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        deleted = (
            self.db.query(Notification)
            .filter(
                and_(
                    Notification.created_at < cutoff_date, Notification.is_read == True
                )
            )
            .delete()
        )

        self.db.commit()
        return deleted

    def get_all_vip_users(self) -> List[User]:
        """Devuelve todos los usuarios con VIP activo."""

        now = datetime.utcnow()
        return (
            self.db.query(User)
            .filter(User.is_vip == True, User.vip_expires.is_not(None), User.vip_expires > now)
            .all()
        )

    async def get_sent_notifications_count(self) -> int:
        """Cuenta notificaciones enviadas"""
        try:
            result = (
                self.db.query(func.count(Notification.id))
                .filter(Notification.is_sent == True)
                .scalar()
            )
            return result or 0
        except Exception as e:
            print(f"Error getting sent notifications count: {e}")
            return 0
   