from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.user_service import UserService
from services.mission_service import MissionService
from services.auction_service import AuctionService
from utils.lucien_voice_enhanced import (
    LucienVoiceEnhanced,
    InteractionPattern,
    UserArchetype,
)
from services.admin_service import AdminService
from models.admin import AdminPermission, AdminLevel
from utils.decorators import admin_required, super_admin_only, admin_only
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import io
import csv

logger = logging.getLogger(__name__)

class CallbackHandlerNarrative:
    """CallbackHandler con sistema narrativo inmersivo integrado"""

    def __init__(self):
        try:
            self.user_service = UserService()
            self.mission_service = MissionService()
            self.auction_service = AuctionService()
            self.lucien = LucienVoiceEnhanced()
            self.admin_service = AdminService()  # ✅ NUEVO
            from services.channel_service import ChannelService
            from services.notification_service import NotificationService
            self.channel_service = ChannelService()
            self.notification_service = NotificationService()
            logger.info("✅ CallbackHandlerNarrative inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando CallbackHandlerNarrative: {e}")
            raise

    async def _send_no_permission_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Envía mensaje cuando el usuario no tiene permisos"""
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "❌ *Acceso Denegado*\n\n"
            "No tienes permisos para acceder a esta función.\n"
            "Contacta a un administrador si crees que esto es un error.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Menú Principal", callback_data="user_main_menu")]]
            ),
        )

    async def _send_error_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        error_msg: str = None,
    ) -> None:
        """Envía mensaje de error genérico"""
        await update.callback_query.answer()
        message = error_msg or "❌ Ha ocurrido un error. Inténtalo de nuevo."
        await update.callback_query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Menú Principal", callback_data="user_main_menu")]]
            ),
        )

    async def _check_admin_permissions(
        self, user_id: int, required_level: str = "admin"
    ) -> bool:
        """Verifica permisos de administrador - CORREGIDO"""
        try:
            admin = await self.admin_service.get_admin_by_user_id(user_id)
            if not admin:
                print(f"No admin found for user_id: {user_id}")
                return False

            if not admin.is_active:
                print(f"Admin not active for user_id: {user_id}")
                return False

            if required_level == "super_admin":
                result = admin.role == "super_admin"
                print(f"Super admin check for {user_id}: {result} (role: {admin.role})")
                return result

            result = admin.role in ["admin", "super_admin"]
            print(f"Admin check for {user_id}: {result} (role: {admin.role})")
            return result
        except Exception as e:
            print(f"Error checking admin permissions for {user_id}: {e}")
            return False

    async def _get_detailed_analytics(self) -> dict:
        """Obtiene estadísticas detalladas del sistema"""
        try:
            stats = {}
            stats["total_users"] = await self.user_service.get_total_users_count()
            stats["active_users_week"] = await self.user_service.get_active_users_count()
            stats["new_users_today"] = await self.user_service.get_new_users_today_count()
            stats["new_users_week"] = await self.user_service.get_new_users_week_count()

            missions_method = getattr(
                self.mission_service, "get_completed_missions_count", None
            )
            stats["missions_completed"] = (
                await missions_method() if missions_method else 0
            )

            stats["avg_level"] = await self.user_service.get_average_level()
            stats["advanced_users"] = await self.user_service.get_advanced_users_count()

            channels_method = getattr(
                self.channel_service, "get_active_channels_count", None
            )
            stats["active_channels"] = (
                await channels_method() if channels_method else 0
            )

            notifications_method = getattr(
                self.notification_service, "get_sent_notifications_count", None
            )
            stats["notifications_sent"] = (
                await notifications_method() if notifications_method else 0
            )

            return stats
        except Exception as e:
            print(f"Error getting analytics: {e}")
            return {}

    async def handle_divan_access(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el acceso al panel de administración - CORREGIDO"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await self._check_admin_permissions(user_id):
            await self._send_no_permission_message(update, context)
            return

        try:
            admin = await self.admin_service.get_admin_by_user_id(user_id)

            keyboard = [
                [
                    InlineKeyboardButton("👥 Gestionar Usuarios", callback_data="admin_users"),
                    InlineKeyboardButton("📺 Canales", callback_data="admin_channels"),
                ],
                [
                    InlineKeyboardButton("🎯 Misiones", callback_data="admin_missions"),
                    InlineKeyboardButton("🏆 Subastas", callback_data="admin_auctions"),
                ],
                [
                    InlineKeyboardButton("🎮 Juegos", callback_data="admin_games"),
                    InlineKeyboardButton("📚 Historia", callback_data="admin_lore"),
                ],
                [
                    InlineKeyboardButton("📊 Estadísticas", callback_data="admin_stats"),
                    InlineKeyboardButton("⚙️ Configuración", callback_data="admin_config"),
                ],
                [
                    InlineKeyboardButton("🔔 Notificaciones", callback_data="admin_notifications"),
                    InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
                ],
            ]

            if admin.role == "super_admin":
                keyboard.extend(
                    [
                        [InlineKeyboardButton("⏳ Solicitudes Pendientes", callback_data="admin_pending_requests")],
                        [InlineKeyboardButton("✅ Aprobar Solicitudes", callback_data="admin_approve_requests")],
                        [InlineKeyboardButton("🎫 Token Personalizado", callback_data="admin_token_custom")],
                    ]
                )

            keyboard.append([InlineKeyboardButton("🔙 Menú Principal", callback_data="user_main_menu")])

            await query.edit_message_text(
                f"🏛️ *Panel de Administración*\n\n"
                f"Bienvenido/a al Diván, {admin.name}\n"
                f"Rol: {admin.role.title()}\n"
                f"Nivel de acceso: {'Completo' if admin.role == 'super_admin' else 'Estándar'}\n\n"
                f"Selecciona una opción:",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al acceder al panel: {str(e)}")

    async def handle_manage_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestión de usuarios - CORREGIDO"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await self._check_admin_permissions(user_id):
            await self._send_no_permission_message(update, context)
            return

        try:
            total_users = await self.user_service.get_total_users_count()
            active_users = await self.user_service.get_active_users_count()
            new_users_today = await self.user_service.get_new_users_today_count()

            keyboard = [
                [InlineKeyboardButton("📋 Lista de Usuarios", callback_data="admin_user_list")],
                [InlineKeyboardButton("🔍 Buscar Usuario", callback_data="admin_search_user")],
                [InlineKeyboardButton("📊 Estadísticas Detalladas", callback_data="admin_user_stats")],
                [InlineKeyboardButton("⚠️ Usuarios Reportados", callback_data="admin_reported_users")],
                [InlineKeyboardButton("🔙 Panel Admin", callback_data="divan_access")],
            ]

            await query.edit_message_text(
                f"👥 *Gestión de Usuarios*\n\n"
                f"📊 **Estadísticas Rápidas:**\n"
                f"• Total de usuarios: {total_users}\n"
                f"• Usuarios activos: {active_users}\n"
                f"• Nuevos hoy: {new_users_today}\n\n"
                f"Selecciona una opción:",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar gestión de usuarios: {str(e)}")

    async def handle_admin_my_activity(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Muestra la actividad del administrador actual"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await self._check_admin_permissions(user_id):
            await self._send_no_permission_message(update, context)
            return

        try:
            admin = await self.admin_service.get_admin_by_user_id(user_id)

            activity_text = (
                f"📋 *Mi Actividad Administrativa*\n\n"
                f"👤 **Información Personal:**\n"
                f"• Nombre: {admin.name}\n"
                f"• Rol: {admin.role.title()}\n"
                f"• Estado: {'Activo' if admin.is_active else 'Inactivo'}\n"
                f"• Registrado: {admin.created_at.strftime('%d/%m/%Y')}\n\n"
                f"📊 **Estadísticas de Actividad:**\n"
                f"• Acciones realizadas hoy: 0\n"
                f"• Total de acciones: 0\n"
                f"• Última actividad: Ahora\n\n"
                f"🎯 **Permisos Actuales:**\n"
            )

            if admin.role == "super_admin":
                activity_text += "• ✅ Acceso completo al sistema\n• ✅ Gestión de administradores\n• ✅ Configuración avanzada"
            else:
                activity_text += "• ✅ Gestión de usuarios\n• ✅ Moderación de contenido\n• ❌ Gestión de administradores"

            keyboard = [
                [InlineKeyboardButton("🔄 Actualizar", callback_data="admin_my_activity")],
                [InlineKeyboardButton("🔙 Volver al Diván", callback_data="divan_access")],
            ]

            await query.edit_message_text(
                activity_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar actividad: {str(e)}")

    async def handle_admin_pending_requests(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Muestra solicitudes pendientes de administrador"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await self._check_admin_permissions(user_id, "super_admin"):
            await self._send_no_permission_message(update, context)
            return

        try:
            pending_requests = await self.admin_service.get_pending_requests()

            if not pending_requests:
                await query.edit_message_text(
                    "📋 *Solicitudes Pendientes*\n\n"
                    "No hay solicitudes pendientes de administrador.\n\n"
                    "Todas las solicitudes han sido procesadas.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🔙 Volver al Diván", callback_data="divan_access")]]
                    ),
                )
                return

            requests_text = "📋 *Solicitudes Pendientes*\n\n"
            keyboard = []

            for i, request in enumerate(pending_requests[:5]):
                requests_text += f"{i+1}. **{request.name}** (ID: {request.user_id})\n"
                requests_text += f"   📅 Solicitado: {request.created_at.strftime('%d/%m/%Y')}\n\n"

                keyboard.append(
                    [
                        InlineKeyboardButton(
                            f"✅ Aprobar #{i+1}", callback_data=f"approve_admin_{request.id}"
                        ),
                        InlineKeyboardButton(
                            f"❌ Rechazar #{i+1}", callback_data=f"reject_admin_{request.id}"
                        ),
                    ]
                )

            keyboard.append([InlineKeyboardButton("🔙 Volver al Diván", callback_data="divan_access")])

            await query.edit_message_text(
                requests_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar solicitudes: {str(e)}")

    async def handle_admin_approve_requests(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Panel para aprobar solicitudes masivamente"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await self._check_admin_permissions(user_id, "super_admin"):
            await self._send_no_permission_message(update, context)
            return

        try:
            keyboard = [
                [InlineKeyboardButton("✅ Aprobar Todas", callback_data="approve_all_requests")],
                [InlineKeyboardButton("📋 Ver Pendientes", callback_data="admin_pending_requests")],
                [InlineKeyboardButton("🔍 Buscar Solicitud", callback_data="search_admin_request")],
                [InlineKeyboardButton("🔙 Volver al Diván", callback_data="divan_access")],
            ]

            await query.edit_message_text(
                "✅ *Aprobación de Solicitudes*\n\n"
                "Gestiona las solicitudes de administrador pendientes.\n\n"
                "⚠️ **Importante:** Los nuevos administradores tendrán acceso "
                "a funciones sensibles del bot. Revisa cuidadosamente antes de aprobar.\n\n"
                "Selecciona una opción:",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar panel de aprobación: {str(e)}")

    async def handle_admin_detailed_analytics(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Analytics detallado del sistema"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await self._check_admin_permissions(user_id):
            await self._send_no_permission_message(update, context)
            return

        try:
            stats = await self._get_detailed_analytics()

            analytics_text = (
                f"📊 *Analytics Detallado*\n\n"
                f"👥 **Usuarios:**\n"
                f"• Total: {stats.get('total_users', 0)}\n"
                f"• Activos (7 días): {stats.get('active_users_week', 0)}\n"
                f"• Nuevos (hoy): {stats.get('new_users_today', 0)}\n"
                f"• Nuevos (semana): {stats.get('new_users_week', 0)}\n\n"
                f"🎯 **Engagement:**\n"
                f"• Misiones completadas: {stats.get('missions_completed', 0)}\n"
                f"• Promedio nivel: {stats.get('avg_level', 0):.1f}\n"
                f"• Usuarios nivel 5+: {stats.get('advanced_users', 0)}\n\n"
                f"📈 **Sistema:**\n"
                f"• Canales activos: {stats.get('active_channels', 0)}\n"
                f"• Notificaciones enviadas: {stats.get('notifications_sent', 0)}\n"
                f"• Uptime: 99.9%"
            )

            keyboard = [
                [InlineKeyboardButton("📊 Exportar Datos", callback_data="export_analytics")],
                [InlineKeyboardButton("🔄 Actualizar", callback_data="admin_detailed_analytics")],
                [InlineKeyboardButton("🔙 Volver al Diván", callback_data="divan_access")],
            ]

            await query.edit_message_text(
                analytics_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar analytics: {str(e)}")

    async def handle_admin_token_custom(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestión de tokens personalizados para super admins"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await self._check_admin_permissions(user_id, "super_admin"):
            await self._send_no_permission_message(update, context)
            return

        try:
            keyboard = [
                [InlineKeyboardButton("🎫 Generar Token", callback_data="generate_custom_token")],
                [InlineKeyboardButton("📋 Ver Tokens Activos", callback_data="view_active_tokens")],
                [InlineKeyboardButton("🗑️ Revocar Token", callback_data="revoke_token")],
                [InlineKeyboardButton("⚙️ Configurar Permisos", callback_data="configure_token_permissions")],
                [InlineKeyboardButton("🔙 Volver al Diván", callback_data="divan_access")],
            ]

            await query.edit_message_text(
                "🎫 *Gestión de Tokens Personalizados*\n\n"
                "Los tokens personalizados permiten acceso programático al bot "
                "y funciones especiales para integraciones.\n\n"
                "⚠️ **Seguridad:** Los tokens otorgan permisos elevados. "
                "Manéjalos con extrema precaución.\n\n"
                "Selecciona una opción:",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar gestión de tokens: {str(e)}")

    async def handle_admin_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestión completa de usuarios (redirige a manage_users)"""
        await self.handle_manage_users(update, context)

    async def handle_admin_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestión de canales"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await self._check_admin_permissions(user_id):
            await self._send_no_permission_message(update, context)
            return

        try:
            # Obtener estadísticas de canales
            active_channels = await self.channel_service.get_active_channels_count() if hasattr(self.channel_service, 'get_active_channels_count') else 0
            pending_requests = await self.channel_service.get_pending_requests_count() if hasattr(self.channel_service, 'get_pending_requests_count') else 0

            keyboard = [
                [InlineKeyboardButton("📋 Lista de Canales", callback_data="admin_channel_list")],
                [InlineKeyboardButton("➕ Agregar Canal", callback_data="admin_channel_add")],
                [InlineKeyboardButton("⏳ Solicitudes Pendientes", callback_data="admin_channel_pending")],
                [InlineKeyboardButton("⚙️ Configurar Canal", callback_data="admin_channel_config")],
                [InlineKeyboardButton("📊 Estadísticas", callback_data="admin_channel_stats")],
                [InlineKeyboardButton("🔙 Panel Admin", callback_data="divan_access")]
            ]

            channels_text = (
                f"📺 *Gestión de Canales*\n\n"
                f"Administra los canales conectados al bot.\n\n"
                f"📊 **Estado actual:**\n"
                f"• Canales activos: {active_channels}\n"
                f"• Solicitudes pendientes: {pending_requests}\n"
                f"• Total gestionados: {active_channels + pending_requests}\n\n"
                f"Selecciona una opción:"
            )

            await query.edit_message_text(
                channels_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar gestión de canales: {str(e)}")

    async def handle_admin_missions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestión de misiones"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await self._check_admin_permissions(user_id):
            await self._send_no_permission_message(update, context)
            return

        try:
            # Obtener estadísticas de misiones
            total_missions = await self.mission_service.get_total_missions_count() if hasattr(self.mission_service, 'get_total_missions_count') else 0
            active_missions = await self.mission_service.get_active_missions_count() if hasattr(self.mission_service, 'get_active_missions_count') else 0
            completed_today = await self.mission_service.get_completed_missions_today() if hasattr(self.mission_service, 'get_completed_missions_today') else 0

            keyboard = [
                [InlineKeyboardButton("📋 Misiones Activas", callback_data="admin_missions_active")],
                [InlineKeyboardButton("➕ Crear Misión", callback_data="admin_mission_create")],
                [InlineKeyboardButton("✏️ Editar Misiones", callback_data="admin_missions_edit")],
                [InlineKeyboardButton("🎯 Asignar Misiones", callback_data="admin_missions_assign")],
                [InlineKeyboardButton("⚙️ Configurar Sistema", callback_data="admin_missions_config")],
                [InlineKeyboardButton("📊 Estadísticas", callback_data="admin_missions_stats")],
                [InlineKeyboardButton("🔙 Panel Admin", callback_data="divan_access")]
            ]

            missions_text = (
                f"🎯 *Gestión de Misiones*\n\n"
                f"Administra el sistema de misiones completo.\n\n"
                f"📊 **Estado actual:**\n"
                f"• Total de misiones: {total_missions}\n"
                f"• Misiones activas: {active_missions}\n"
                f"• Completadas hoy: {completed_today}\n\n"
                f"Selecciona una opción:"
            )

            await query.edit_message_text(
                missions_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar gestión de misiones: {str(e)}")

    async def handle_admin_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestión de juegos"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await self._check_admin_permissions(user_id):
            await self._send_no_permission_message(update, context)
            return

        try:
            # Obtener estadísticas de juegos
            games_played_today = await self.game_service.get_games_played_today() if hasattr(self, 'game_service') and hasattr(self.game_service, 'get_games_played_today') else 0
            total_games = await self.game_service.get_total_games_count() if hasattr(self, 'game_service') and hasattr(self.game_service, 'get_total_games_count') else 0

            keyboard = [
                [InlineKeyboardButton("🎮 Juegos Activos", callback_data="admin_games_active")],
                [InlineKeyboardButton("➕ Añadir Juego", callback_data="admin_game_add")],
                [InlineKeyboardButton("⚙️ Configurar Juegos", callback_data="admin_games_config")],
                [InlineKeyboardButton("🏆 Gestionar Ranking", callback_data="admin_games_ranking")],
                [InlineKeyboardButton("🎯 Ajustar Dificultad", callback_data="admin_games_difficulty")],
                [InlineKeyboardButton("📊 Estadísticas", callback_data="admin_games_stats")],
                [InlineKeyboardButton("🔙 Panel Admin", callback_data="divan_access")]
            ]

            games_text = (
                f"🎮 *Gestión de Juegos*\n\n"
                f"Administra todos los juegos del sistema.\n\n"
                f"📊 **Estado actual:**\n"
                f"• Partidas jugadas hoy: {games_played_today}\n"
                f"• Total de partidas: {total_games}\n"
                f"• Juegos disponibles: Trivia, Números, Matemáticas\n\n"
                f"Selecciona una opción:"
            )

            await query.edit_message_text(
                games_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar gestión de juegos: {str(e)}")

    async def handle_admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Estadísticas generales (redirige a analytics detallado)"""
        await self.handle_admin_detailed_analytics(update, context)

    async def handle_admin_auctions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestión de subastas"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await self._check_admin_permissions(user_id):
            await self._send_no_permission_message(update, context)
            return

        try:
            # Obtener estadísticas de subastas
            active_auctions = 0
            total_auctions = 0
            if hasattr(self, 'auction_service'):
                active_auctions = await self.auction_service.get_active_auctions_count() if hasattr(self.auction_service, 'get_active_auctions_count') else 0
                total_auctions = await self.auction_service.get_total_auctions_count() if hasattr(self.auction_service, 'get_total_auctions_count') else 0

            keyboard = [
                [InlineKeyboardButton("📋 Subastas Activas", callback_data="admin_auctions_active")],
                [InlineKeyboardButton("➕ Crear Subasta", callback_data="admin_auction_create")],
                [InlineKeyboardButton("🏆 Historial", callback_data="admin_auctions_history")],
                [InlineKeyboardButton("💰 Gestionar Pujas", callback_data="admin_auctions_bids")],
                [InlineKeyboardButton("⚙️ Configuración", callback_data="admin_auctions_config")],
                [InlineKeyboardButton("📊 Estadísticas", callback_data="admin_auctions_stats")],
                [InlineKeyboardButton("🔙 Panel Admin", callback_data="divan_access")]
            ]

            auctions_text = (
                f"🏆 *Gestión de Subastas VIP*\n\n"
                f"Administra el sistema de subastas exclusivas.\n\n"
                f"📊 **Estado actual:**\n"
                f"• Subastas activas: {active_auctions}\n"
                f"• Total realizadas: {total_auctions}\n"
                f"• Sistema: {'Activo' if active_auctions > 0 else 'Inactivo'}\n\n"
                f"Selecciona una opción:"
            )

            await query.edit_message_text(
                auctions_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar gestión de subastas: {str(e)}")

    async def handle_admin_lore(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestión de historia/narrativa"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await self._check_admin_permissions(user_id):
            await self._send_no_permission_message(update, context)
            return

        try:
            keyboard = [
                [InlineKeyboardButton("📚 Historia Actual", callback_data="admin_lore_current")],
                [InlineKeyboardButton("✏️ Editar Narrativa", callback_data="admin_lore_edit")],
                [InlineKeyboardButton("🎭 Gestionar Arquetipos", callback_data="admin_lore_archetypes")],
                [InlineKeyboardButton("🔮 Triggers Narrativos", callback_data="admin_lore_triggers")],
                [InlineKeyboardButton("📖 Pistas y Objetos", callback_data="admin_lore_clues")],
                [InlineKeyboardButton("🌟 Estados Narrativos", callback_data="admin_lore_states")],
                [InlineKeyboardButton("🔙 Panel Admin", callback_data="divan_access")]
            ]

            lore_text = (
                f"📚 *Gestión de Historia*\n\n"
                f"Administra la narrativa completa y arquetipos del sistema.\n\n"
                f"🎭 **Componentes:**\n"
                f"• Arquetipos activos\n"
                f"• Estados narrativos\n"
                f"• Triggers y eventos\n"
                f"• Pistas y objetos\n\n"
                f"Selecciona una opción:"
            )

            await query.edit_message_text(
                lore_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar gestión de historia: {str(e)}")

    async def handle_admin_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Configuración general del sistema"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await self._check_admin_permissions(user_id, "super_admin"):
            await self._send_no_permission_message(update, context)
            return

        try:
            keyboard = [
                [InlineKeyboardButton("⚙️ Configuración General", callback_data="admin_config_general")],
                [InlineKeyboardButton("🎯 Niveles y Experiencia", callback_data="admin_config_levels")],
                [InlineKeyboardButton("💰 Sistema de Economía", callback_data="admin_config_economy")],
                [InlineKeyboardButton("🔔 Notificaciones", callback_data="admin_config_notifications")],
                [InlineKeyboardButton("👑 Configuración VIP", callback_data="admin_config_vip")],
                [InlineKeyboardButton("🛡️ Seguridad", callback_data="admin_config_security")],
                [InlineKeyboardButton("🔙 Panel Admin", callback_data="divan_access")]
            ]

            config_text = (
                f"⚙️ *Configuración del Sistema*\n\n"
                f"Ajusta la configuración global del bot.\n\n"
                f"⚠️ **Precaución:** Los cambios aquí afectan todo el sistema.\n\n"
                f"🔧 **Categorías disponibles:**\n"
                f"• Configuración general\n"
                f"• Sistema de niveles\n"
                f"• Economía y besitos\n"
                f"• Notificaciones\n"
                f"• Membresía VIP\n"
                f"• Seguridad\n\n"
                f"Selecciona una opción:"
            )

            await query.edit_message_text(
                config_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar configuración: {str(e)}")

    async def handle_admin_notifications(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestión de notificaciones"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await self._check_admin_permissions(user_id):
            await self._send_no_permission_message(update, context)
            return

        try:
            # Obtener estadísticas de notificaciones
            active_notifications = await self.notification_service.get_active_notifications_count() if hasattr(self.notification_service, 'get_active_notifications_count') else 0
            sent_today = await self.notification_service.get_sent_today_count() if hasattr(self.notification_service, 'get_sent_today_count') else 0

            keyboard = [
                [InlineKeyboardButton("📋 Notificaciones Activas", callback_data="admin_notifications_active")],
                [InlineKeyboardButton("➕ Crear Notificación", callback_data="admin_notification_create")],
                [InlineKeyboardButton("📅 Programar Envío", callback_data="admin_notification_schedule")],
                [InlineKeyboardButton("🎯 Notificaciones Dirigidas", callback_data="admin_notification_targeted")],
                [InlineKeyboardButton("📊 Estadísticas", callback_data="admin_notifications_stats")],
                [InlineKeyboardButton("⚙️ Configurar", callback_data="admin_notifications_config")],
                [InlineKeyboardButton("🔙 Panel Admin", callback_data="divan_access")]
            ]

            notifications_text = (
                f"🔔 *Gestión de Notificaciones*\n\n"
                f"Administra las notificaciones del sistema.\n\n"
                f"📊 **Estado actual:**\n"
                f"• Notificaciones activas: {active_notifications}\n"
                f"• Enviadas hoy: {sent_today}\n"
                f"• Sistema: Activo\n\n"
                f"Selecciona una opción:"
            )

            await query.edit_message_text(
                notifications_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar notificaciones: {str(e)}")

    async def handle_admin_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mensajes masivos"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await self._check_admin_permissions(user_id, "super_admin"):
            await self._send_no_permission_message(update, context)
            return

        try:
            # Obtener estadísticas de usuarios para broadcast
            total_users = await self.user_service.get_total_users_count()
            vip_users = await self.user_service.get_vip_users_count()
            active_users = await self.user_service.get_active_users_count()

            keyboard = [
                [InlineKeyboardButton("📢 Mensaje General", callback_data="admin_broadcast_general")],
                [InlineKeyboardButton("👑 Solo VIP", callback_data="admin_broadcast_vip")],
                [InlineKeyboardButton("🎯 Por Nivel", callback_data="admin_broadcast_level")],
                [InlineKeyboardButton("🏆 Por Arquetipo", callback_data="admin_broadcast_archetype")],
                [InlineKeyboardButton("📱 Usuarios Activos", callback_data="admin_broadcast_active")],
                [InlineKeyboardButton("📊 Historial", callback_data="admin_broadcast_history")],
                [InlineKeyboardButton("🔙 Panel Admin", callback_data="divan_access")]
            ]

            broadcast_text = (
                f"📢 *Mensajes Masivos*\n\n"
                f"Envía mensajes a grupos específicos de usuarios.\n\n"
                f"👥 **Audiencia disponible:**\n"
                f"• Total usuarios: {total_users}\n"
                f"• Usuarios VIP: {vip_users}\n"
                f"• Usuarios activos: {active_users}\n\n"
                f"⚠️ **Importante:** Usa con responsabilidad para evitar spam.\n\n"
                f"Selecciona el tipo de mensaje:"
            )

            await query.edit_message_text(
                broadcast_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar broadcast: {str(e)}")

    async def handle_admin_user_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra lista paginada de usuarios"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await self._check_admin_permissions(user_id):
            await self._send_no_permission_message(update, context)
            return

        try:
            page = int(context.user_data.get('user_list_page', 0))
            users = await self.user_service.get_users_paginated(page, 10)

            if not users:
                await query.edit_message_text(
                    "👥 *Lista de Usuarios*\n\n"
                    "No se encontraron usuarios en esta página.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🔙 Volver", callback_data="manage_users")]]
                    ),
                )
                return

            user_list_text = f"👥 *Lista de Usuarios* (Página {page + 1})\n\n"

            for i, user in enumerate(users):
                status = "🟢" if getattr(user, "is_active", True) else "🔴"
                user_list_text += f"{status} **{getattr(user, 'name', 'User')}** (ID: {getattr(user, 'user_id', user.id)})\n"
                user_list_text += f"   Nivel: {getattr(user, 'level', 0)} | Arquetipo: {getattr(user, 'archetype', 'N/A')}\n"
                created_at = getattr(user, 'created_at', datetime.utcnow())
                user_list_text += f"   Registro: {created_at.strftime('%d/%m/%Y')}\n\n"

            keyboard = []
            nav_buttons = []

            if page > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️ Anterior", callback_data="user_list_prev"))

            nav_buttons.append(InlineKeyboardButton("➡️ Siguiente", callback_data="user_list_next"))

            if nav_buttons:
                keyboard.append(nav_buttons)

            keyboard.extend(
                [
                    [InlineKeyboardButton("🔍 Buscar Usuario", callback_data="admin_search_user")],
                    [InlineKeyboardButton("🔙 Volver", callback_data="manage_users")],
                ]
            )

            await query.edit_message_text(
                user_list_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar lista de usuarios: {str(e)}")

    async def handle_export_analytics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Exporta analytics en formato CSV"""
        query = update.callback_query
        user_id = query.from_user.id

        if not await self._check_admin_permissions(user_id):
            await self._send_no_permission_message(update, context)
            return

        try:
            await query.answer("📊 Generando reporte...")

            stats = await self._get_detailed_analytics()

            output = io.StringIO()
            writer = csv.writer(output)

            writer.writerow(["Métrica", "Valor", "Fecha"])
            writer.writerow([
                "Total Usuarios",
                stats.get("total_users", 0),
                datetime.now().strftime("%Y-%m-%d"),
            ])
            writer.writerow([
                "Usuarios Activos",
                stats.get("active_users_week", 0),
                datetime.now().strftime("%Y-%m-%d"),
            ])
            writer.writerow([
                "Nuevos Usuarios Hoy",
                stats.get("new_users_today", 0),
                datetime.now().strftime("%Y-%m-%d"),
            ])
            writer.writerow([
                "Misiones Completadas",
                stats.get("missions_completed", 0),
                datetime.now().strftime("%Y-%m-%d"),
            ])

            csv_content = output.getvalue()
            output.close()

            csv_file = io.BytesIO(csv_content.encode("utf-8"))
            csv_file.name = f"dianabot_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=csv_file,
                caption="📊 Reporte de Analytics generado exitosamente",
            )

            await query.edit_message_text(
                "✅ *Exportación Completada*\n\n"
                "El reporte de analytics ha sido enviado como archivo CSV.\n\n"
                "El archivo contiene todas las métricas principales del sistema.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔙 Volver a Analytics", callback_data="admin_detailed_analytics")]]
                ),
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al exportar analytics: {str(e)}")

    async def handle_user_list_navigation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja la navegación en la lista de usuarios"""
        query = update.callback_query

        current_page = int(context.user_data.get('user_list_page', 0))

        if query.data == 'user_list_next':
            context.user_data['user_list_page'] = current_page + 1
        elif query.data == 'user_list_prev':
            context.user_data['user_list_page'] = max(0, current_page - 1)

        await self.handle_admin_user_list(update, context)

    async def start_narrative(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Inicia la narrativa y asigna misiones diarias"""

        user_id = update.effective_user.id

        # Lógica inicial de narrativa (placeholder)

        self.mission_service.create_daily_missions_for_user(user_id)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Router principal con narrativa inmersiva"""
        
        try:
            query = update.callback_query
            await query.answer()

            user_data = {
                "telegram_id": query.from_user.id,
                "username": query.from_user.username,
                "first_name": query.from_user.first_name or "Usuario",
                "last_name": query.from_user.last_name,
            }

            logger.info(f"🔍 Callback narrativo: {query.data} de {user_data['first_name']}")

            # Obtener usuario y estado narrativo
            user = self.user_service.get_or_create_user(user_data)
            narrative_state = self.user_service.get_or_create_narrative_state(user.id)

            callback_data = query.data

            # Manejar patrones de callback
            if callback_data.startswith('trivia_answer_'):
                return await self.handle_trivia_answer(update, context)
            elif callback_data.startswith('math_answer_'):
                return await self.handle_math_answer(update, context)

            routing = {
                'trivia_answer_0': self.handle_trivia_answer,
                'trivia_answer_1': self.handle_trivia_answer,
                'trivia_answer_2': self.handle_trivia_answer,
                'trivia_answer_3': self.handle_trivia_answer,
                'math_answer_0': self.handle_math_answer,
                'math_answer_1': self.handle_math_answer,
                'math_answer_2': self.handle_math_answer,
                'math_answer_3': self.handle_math_answer,
                'backpack_view_clues': self.handle_backpack_view_clues,
                'backpack_progress': self.handle_backpack_progress,
                # Callbacks faltantes
                'user_profile': self.handle_user_profile,
                'user_main_menu': self.handle_user_main_menu,
                'backpack_categories': self.handle_backpack_categories,
                'backpack_combine': self.handle_backpack_combine,
                'category_communication': self.handle_category_communication,
                'profile_detailed_stats': self.handle_profile_detailed_stats,
                'category_development': self.handle_category_development,
                'category_seduction': self.handle_category_seduction,
                'missions_refresh': self.handle_missions_refresh,
                'back_to_menu': self.handle_back_to_menu,
            }

            if callback_data in routing:
                return await routing[callback_data](update, context)

            # === NARRATIVA NIVEL 1 ===
            if callback_data == "discover_more" or callback_data == "level1_scene2":
                await self._handle_level1_scene2(update, context, user, narrative_state)
            elif callback_data == "react_to_channel":
                await self._handle_reaction_challenge(update, context, user, narrative_state)
            elif callback_data.startswith("reaction_"):
                await self._handle_reaction_result(update, context, user, narrative_state, callback_data)
            
            # === NAVEGACIÓN NARRATIVA ===
            elif callback_data == "back_to_story":
                await self._handle_back_to_current_scene(update, context, user, narrative_state)
            elif callback_data == "continue_journey":
                await self.handle_user_main_menu(update, context)
            
            # === CALLBACKS EXISTENTES (conservados) ===
            elif callback_data == "profile":
                await self._show_profile_narrative(update, context, user, narrative_state)
            elif callback_data == "missions":
                await self._handle_missions_original(update, context, user, narrative_state)
            elif callback_data == "back_to_menu":
                await self._show_main_menu_narrative(update, context, user, narrative_state)

            # === CALLBACKS DEL SISTEMA ORIGINAL ===
            elif callback_data == "premium":
                await self._handle_premium_original(update, context, user, narrative_state)

            # === CALLBACKS NARRATIVOS ===
            elif callback_data == "narrative_progress":
                await self._handle_narrative_progress(update, context, user, narrative_state)
            elif callback_data == "review_clues":
                await self._handle_unknown_callback_narrative(update, context, "review_clues")
            elif callback_data == "talk_to_diana":
                await self._handle_unknown_callback_narrative(update, context, "talk_to_diana")
            elif callback_data == "settings":
                await self._handle_unknown_callback_narrative(update, context, "settings")
            elif callback_data == "user_main_menu":
                await self.handle_user_main_menu(update, context)
            elif callback_data == "user_profile":
                await self.handle_user_profile(update, context)
            elif callback_data == "user_missions":
                await self.handle_user_missions(update, context)
            elif callback_data == "user_games":
                await self.handle_user_games(update, context)
            elif callback_data == "user_backpack":
                await self.handle_user_backpack(update, context)
            elif callback_data == "backpack_categories":
                await self.handle_backpack_categories(update, context)
            elif callback_data == "backpack_combine":
                await self.handle_backpack_combine(update, context)
            elif callback_data == "user_daily_gift":
                await self.handle_user_daily_gift(update, context)
            elif callback_data == "claim_daily_gift":
                await self.handle_claim_daily_gift(update, context)
            elif callback_data == "user_leaderboard":
                await self.handle_user_leaderboard(update, context)
            elif callback_data == "user_auctions":
                await self.handle_user_auctions(update, context)

            # === CALLBACKS DE ADMINISTRACIÓN ===
            elif callback_data == "admin_panel":
                await self._show_admin_panel(update, context, user, narrative_state)
            elif callback_data == "generate_vip_token":
                await self._handle_generate_vip_token(update, context, user, narrative_state)
            elif callback_data == "manage_channels":
                await self._handle_manage_channels(update, context, user, narrative_state)
            elif callback_data == "admin_analytics":
                await self._handle_admin_analytics(update, context, user, narrative_state)
            elif callback_data == "manage_admins":
                await self._handle_manage_admins(update, context, user, narrative_state)
            elif callback_data == "divan_access":
                await self.handle_divan_access(update, context)
            elif callback_data == "admin_users":
                await self.handle_admin_users(update, context)
            elif callback_data == "admin_channels":
                await self.handle_admin_channels(update, context)
            elif callback_data == "admin_missions":
                await self.handle_admin_missions(update, context)
            elif callback_data == "admin_games":
                await self.handle_admin_games(update, context)
            elif callback_data == "admin_auctions":
                await self.handle_admin_auctions(update, context)
            elif callback_data == "admin_lore":
                await self.handle_admin_lore(update, context)
            elif callback_data == "admin_config":
                await self.handle_admin_config(update, context)
            elif callback_data == "admin_notifications":
                await self.handle_admin_notifications(update, context)
            elif callback_data == "admin_broadcast":
                await self.handle_admin_broadcast(update, context)
            elif callback_data == "manage_users":
                await self.handle_manage_users(update, context)
            elif callback_data == "admin_my_activity":
                await self.handle_admin_my_activity(update, context)
            elif callback_data == "admin_pending_requests":
                await self.handle_admin_pending_requests(update, context)
            elif callback_data == "admin_approve_requests":
                await self.handle_admin_approve_requests(update, context)
            elif callback_data == "admin_detailed_analytics":
                await self.handle_admin_detailed_analytics(update, context)
            elif callback_data == "admin_stats":
                await self.handle_admin_stats(update, context)
            elif callback_data == "admin_token_custom":
                await self.handle_admin_token_custom(update, context)
            elif callback_data == "admin_user_list":
                await self.handle_admin_user_list(update, context)
            elif callback_data == "export_analytics":
                await self.handle_export_analytics(update, context)
            elif callback_data in ["user_list_next", "user_list_prev"]:
                await self.handle_user_list_navigation(update, context)
            elif callback_data.startswith("admin_"):
                await self._handle_admin_action(update, context, user, narrative_state, callback_data)

            # === CATCH-ALL ===
            else:
                await self._handle_unknown_callback_narrative(update, context, callback_data)

        except Exception as e:
            logger.error(f"❌ Error en handle_callback narrativo: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    # === NIVEL 1 - IMPLEMENTACIÓN COMPLETA ===

    async def _handle_level1_scene2(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Nivel 1, Escena 2 - Lucien presenta el primer desafío"""
        
        try:
            first_name = getattr(user, 'first_name', 'Usuario')
            
            # Detectar arquetipo del usuario (simplificado por ahora)
            user_archetype = self._detect_user_archetype(user, narrative_state)
            
            # Obtener mensaje de Lucien
            lucien_message = self.lucien.get_lucien_level1_scene2_intro(first_name, user_archetype)

            # Botones para el desafío
            keyboard = [
                [InlineKeyboardButton("💫 Reaccionar al último mensaje", callback_data="react_to_channel")],
                [InlineKeyboardButton("🤔 ¿Por qué debo reaccionar?", callback_data="why_react")],
                [InlineKeyboardButton("😏 No me gusta que me ordenen", callback_data="rebellious_response")],
                [InlineKeyboardButton("⬅️ Volver con Diana", callback_data="back_to_diana")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                lucien_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )

            # Actualizar estado narrativo
            await self._update_narrative_progress(user.id, "level1_scene2_presented")

        except Exception as e:
            logger.error(f"❌ Error en _handle_level1_scene2: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _handle_reaction_challenge(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Maneja el desafío de reacción al canal"""
        
        try:
            first_name = getattr(user, 'first_name', 'Usuario')

            # Simular el desafío de reacción
            challenge_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire expectante]*

Perfecto, {first_name}. Ahora viene la parte... interesante.

*[Señalando hacia el canal]*

Ve al último mensaje del canal y reacciona. Pero recuerda...

{self.lucien.EMOJIS['diana']} *[Diana susurra desde las sombras]*

"*No es solo una reacción. Es una declaración de intención.*"

*[Con misterio]*

"*Elige el emoji que mejor represente por qué estás aquí.*"

⏰ **Tienes 5 minutos para decidir.**

Diana estará... observando.
            """.strip()

            # Botones de simulación (en implementación real sería tracking del canal)
            keyboard = [
                [InlineKeyboardButton("❤️ Reaccionar con corazón", callback_data="reaction_heart")],
                [InlineKeyboardButton("🔥 Reaccionar con fuego", callback_data="reaction_fire")],
                [InlineKeyboardButton("👀 Reaccionar con ojos", callback_data="reaction_eyes")],
                [InlineKeyboardButton("⏰ Necesito más tiempo", callback_data="reaction_delay")],
                [InlineKeyboardButton("❌ No quiero reaccionar", callback_data="reaction_refuse")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                challenge_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )

            # Guardar timestamp del desafío
            await self._save_challenge_timestamp(user.id, "reaction_challenge")

        except Exception as e:
            logger.error(f"❌ Error en _handle_reaction_challenge: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _handle_reaction_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any, callback_data: str) -> None:
        """Procesa el resultado de la reacción del usuario"""
        
        try:
            first_name = getattr(user, 'first_name', 'Usuario')
            
            # Extraer tipo de reacción
            reaction_type = callback_data.replace("reaction_", "")
            
            # Calcular tiempo de respuesta
            reaction_time = await self._calculate_reaction_time(user.id, "reaction_challenge")
            
            # Determinar patrón de reacción
            if reaction_time < 30:  # Menos de 30 segundos
                time_pattern = "immediate"
            elif reaction_time < 180:  # Menos de 3 minutos
                time_pattern = "thoughtful"
            else:
                time_pattern = "delayed"

            # Obtener respuesta de Diana según la reacción
            if reaction_type in ["heart", "fire", "eyes"]:
                diana_response = self.lucien.get_diana_reaction_response(time_pattern, first_name)
            elif reaction_type == "delay":
                diana_response = self._get_delay_response(first_name)
            else:  # refuse
                diana_response = self._get_refusal_response(first_name)

            # Mostrar respuesta de Diana
            full_message = f"""
{diana_response['diana_message']}

{diana_response['lucien_comment']}

{self._get_reward_message(diana_response['reward_type'])}
            """.strip()

            # Botones según el resultado
            if reaction_type != "refuse":
                keyboard = [
                    [InlineKeyboardButton("🎁 Abrir Mochila del Viajero", callback_data="open_traveler_bag")],
                    [InlineKeyboardButton("🗺️ Examinar la pista", callback_data="examine_clue")],
                    [InlineKeyboardButton("💬 Hablar con Diana", callback_data="talk_to_diana")],
                    [InlineKeyboardButton("➡️ Continuar el viaje", callback_data="user_main_menu")],
                ]
            else:
                keyboard = [
                    [InlineKeyboardButton("🔄 Reconsiderar mi decisión", callback_data="react_to_channel")],
                    [InlineKeyboardButton("💭 Necesito pensar más", callback_data="thinking_time")],
                    [InlineKeyboardButton("⬅️ Volver al inicio", callback_data="back_to_menu")],
                ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                full_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )

            # Actualizar progreso narrativo
            await self._update_narrative_progress(user.id, f"level1_reaction_{reaction_type}")
            await self._update_user_archetype(user.id, reaction_type, time_pattern)

        except Exception as e:
            logger.error(f"❌ Error en _handle_reaction_result: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    # === MÉTODOS AUXILIARES NARRATIVOS ===

    def _detect_user_archetype(self, user: Any, narrative_state: Any) -> UserArchetype:
        """Detecta el arquetipo del usuario basado en comportamiento"""
        
        # Lógica simplificada - en implementación real sería más sofisticada
        try:
            # Analizar historial de interacciones
            interaction_count = getattr(narrative_state, 'interaction_count', 0)
            
            if interaction_count < 3:
                return UserArchetype.UNDEFINED
            
            # Por ahora retornamos Explorer como default
            return UserArchetype.EXPLORER
            
        except Exception as e:
            logger.error(f"Error detectando arquetipo: {e}")
            return UserArchetype.UNDEFINED

    async def _calculate_reaction_time(self, user_id: int, challenge_type: str) -> int:
        """Calcula el tiempo de reacción del usuario"""
        
        try:
            # En implementación real, obtendríamos el timestamp guardado
            # Por ahora simulamos
            return 45  # 45 segundos como ejemplo
            
        except Exception as e:
            logger.error(f"Error calculando tiempo de reacción: {e}")
            return 60

    async def _save_challenge_timestamp(self, user_id: int, challenge_type: str) -> None:
        """Guarda timestamp del desafío"""
        
        try:
            # En implementación real, guardaríamos en BD
            timestamp = datetime.utcnow()
            logger.info(f"📝 Challenge timestamp guardado: {user_id} - {challenge_type} - {timestamp}")
            
        except Exception as e:
            logger.error(f"Error guardando timestamp: {e}")

    async def _update_narrative_progress(self, user_id: int, progress_key: str) -> None:
        """Actualiza el progreso narrativo del usuario"""
        
        try:
            # En implementación real, actualizaríamos UserNarrativeState
            logger.info(f"📈 Progreso narrativo actualizado: {user_id} - {progress_key}")
            
        except Exception as e:
            logger.error(f"Error actualizando progreso narrativo: {e}")

    async def _update_user_archetype(self, user_id: int, reaction_type: str, time_pattern: str) -> None:
        """Actualiza el arquetipo del usuario basado en su comportamiento"""
        
        try:
            # Lógica para determinar arquetipo basado en reacción
            if time_pattern == "immediate" and reaction_type in ["heart", "fire"]:
                archetype = UserArchetype.DIRECT
            elif time_pattern == "thoughtful":
                archetype = UserArchetype.ANALYTICAL
            elif reaction_type == "eyes":
                archetype = UserArchetype.EXPLORER
            else:
                archetype = UserArchetype.UNDEFINED

            logger.info(f"🎭 Arquetipo actualizado: {user_id} - {archetype.value}")
            
        except Exception as e:
            logger.error(f"Error actualizando arquetipo: {e}")

    def _get_delay_response(self, first_name: str) -> Dict[str, str]:
        """Respuesta cuando el usuario pide más tiempo"""
        
        return {
            "diana_message": f"""
{self.lucien.EMOJIS['diana']} *[Con comprensión paciente]*

{first_name}... necesitas más tiempo.

*[Con sabiduría]*

No hay prisa en las decisiones que importan. Tómate el tiempo que necesites.

*[Con misterio]*

Estaré aquí cuando estés listo para dar ese paso.""",
            
            "lucien_comment": f"""
{self.lucien.EMOJIS['lucien']} *[Con aprobación reluctante]*

"*Al menos {first_name} es honesto sobre sus... limitaciones temporales.*"

*[Con aire profesional]*

"*Diana aprecia la honestidad más que la falsa bravura.*"
""",
            "reward_type": "patience_acknowledged"
        }

    def _get_refusal_response(self, first_name: str) -> Dict[str, str]:
        """Respuesta cuando el usuario se niega a reaccionar"""

        return {
            "diana_message": f"""
{self.lucien.EMOJIS['diana']} *[Con decepción sutil]*

{first_name}... decidiste no participar.

*[Con aire reflexivo]*

Interesante. A veces la resistencia dice más que la obediencia.

*[Con paciencia enigmática]*

Pero recuerda... algunas puertas solo se abren una vez.""",

            "lucien_comment": f"""
{self.lucien.EMOJIS['lucien']} *[Con sarcasmo palpable]*

"*Ah, qué sorpresa... otro que se paraliza ante el primer desafío real.*"

*[Con desdén elegante]*

"*Diana es paciente, yo... considerably less so.*"
""",
            "reward_type": "refusal_consequence"
        }

    def _get_reward_message(self, reward_type: str) -> str:
        """Genera mensaje de recompensa según el tipo"""
        
        reward_content = self.lucien.get_reward_content(reward_type, UserArchetype.UNDEFINED)
        
        return f"""
🎁 **{reward_content['title']}**

*{reward_content['description']}*

**Contenido:** {reward_content['content']}
**Rareza:** {reward_content['rarity']}
        """.strip()

    # === CALLBACKS NARRATIVOS ADICIONALES ===

    async def _handle_open_traveler_bag(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Maneja la apertura de la Mochila del Viajero"""
        
        try:
            first_name = getattr(user, 'first_name', 'Usuario')

            bag_message = f"""
{self.lucien.EMOJIS['elegant']} **Mochila del Viajero Abierta**

{self.lucien.EMOJIS['lucien']} *[Con ceremonia]*

"*Veamos qué ha preparado Diana para ti, {first_name}...*"

*[Abriendo la mochila con dramatismo]*

🗺️ **Fragmento de Mapa Misterioso**
*Una pieza de pergamino antiguo con símbolos extraños*

📜 **Nota Personal de Diana:**
*"Para {first_name}: Este mapa está incompleto... intencionalmente. La otra mitad existe donde las reglas cambian. - D"*

🔑 **Llave Simbólica**
*Una pequeña llave dorada con la inscripción: "Para puertas que no todos pueden ver"*

{self.lucien.EMOJIS['diana']} *[Diana aparece brevemente]*

"*La verdadera pregunta no es qué contiene la mochila... sino si estás preparado para usar lo que hay dentro.*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("🗺️ Examinar el mapa", callback_data="examine_map")],
                [InlineKeyboardButton("📜 Leer nota completa", callback_data="read_diana_note")],
                [InlineKeyboardButton("🔑 Inspeccionar la llave", callback_data="inspect_key")],
                [InlineKeyboardButton("💭 ¿Qué significa todo esto?", callback_data="ask_meaning")],
                [InlineKeyboardButton("➡️ Continuar el viaje", callback_data="user_main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                bag_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_open_traveler_bag: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _handle_examine_map(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Examina el fragmento de mapa"""
        
        try:
            first_name = getattr(user, 'first_name', 'Usuario')

            map_message = f"""
🗺️ **Fragmento de Mapa Analizado**

{self.lucien.EMOJIS['lucien']} *[Con aire de detective]*

"*Interesante, {first_name}... este mapa no señala un lugar físico.*"

*[Examinando con lupa imaginaria]*

**Lo que puedes ver:**
• Símbolos que parecen... emociones
• Caminos que se bifurcan según decisiones
• Una X marcada en un lugar llamado "Comprensión Mutua"
• Coordenadas que no son geográficas: "Vulnerabilidad 40°, Confianza 60°"

{self.lucien.EMOJIS['diana']} *[Susurrando desde las sombras]*

"*Este mapa no te lleva a un lugar, {first_name}... te lleva a un estado de ser.*"

*[Con misterio profundo]*

"*Y la otra mitad... solo aparece cuando demuestras que puedes manejar esta.*"

{self.lucien.EMOJIS['lucien']} *[Con sarcasmo]*

"*Típico de Diana... hasta sus mapas son... filosóficos.*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("🧭 ¿Cómo uso este mapa?", callback_data="how_to_use_map")],
                [InlineKeyboardButton("❓ ¿Dónde está la otra mitad?", callback_data="where_other_half")],
                [InlineKeyboardButton("💡 Creo que entiendo", callback_data="understand_map")],
                [InlineKeyboardButton("🔙 Volver a la mochila", callback_data="open_traveler_bag")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                map_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_examine_map: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    # === MENÚS PRINCIPALES CON NARRATIVA ===

    async def _show_main_menu_narrative(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el menú principal narrativo - CORREGIDO"""
        try:
            user_id = update.callback_query.from_user.id
            user = self.user_service.get_user_by_telegram_id(user_id)

            if not user:
                await self._send_error_message(update, context, "Usuario no encontrado")
                return

            main_menu_text = (
                f"🎭 *DianaBot - Menu Principal*\n\n"
                f"*Lucien te recibe con elegancia...*\n\n"
                f"Ah, {user.first_name}! Diana me comento que podrias venir.\n\n"
                f"📊 **Tu estado actual:**\n"
                f"• Nivel: {user.level}\n"
                f"• Besitos: {user.besitos}\n"
                f"• Estado: {'👑 VIP' if user.is_vip else '🌟 Miembro'}\n\n"
                f"¿Que deseas hacer?"
            )

            keyboard = [
                [
                    InlineKeyboardButton("👤 Mi Perfil", callback_data="user_profile"),
                    InlineKeyboardButton("🎯 Misiones", callback_data="user_missions")
                ],
                [
                    InlineKeyboardButton("🎮 Juegos", callback_data="user_games"),
                    InlineKeyboardButton("🎒 Mochila", callback_data="user_backpack")
                ],
                [
                    InlineKeyboardButton("🎁 Regalo Diario", callback_data="user_daily_gift"),
                    InlineKeyboardButton("🏆 Ranking", callback_data="user_leaderboard")
                ]
            ]

            try:
                admin = await self.admin_service.get_admin_by_user_id(user_id)
                if admin and admin.is_active:
                    keyboard.append([InlineKeyboardButton("🏛️ Panel de Administración", callback_data="divan_access")])
            except:
                pass

            if user.is_vip or user.level >= 5:
                keyboard.append([InlineKeyboardButton("🏆 Subastas VIP", callback_data="user_auctions")])

            await update.callback_query.edit_message_text(
                main_menu_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            logger.error(f"❌ Error en _show_main_menu_narrative: {e}")
            await self._send_error_message(update, context, f"Error al cargar menu principal: {str(e)}")

    async def _show_profile_narrative(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Perfil con contexto narrativo"""
        
        try:
            first_name = getattr(user, 'first_name', 'Usuario')
            
            # Obtener datos del usuario
            level = getattr(user, 'level', 1)
            besitos = getattr(user, 'besitos', 0)
            trust_level = getattr(narrative_state, 'diana_trust_level', 0)
            
            profile_message = f"""
{self.lucien.EMOJIS['lucien']} **Expediente Personal de {first_name}**

*[Consultando un elegante dossier]*

"*Veamos tu... evolución hasta ahora.*"

📊 **Estadísticas de Progreso:**
• **Nivel Narrativo:** {level}
• **Besitos de Diana:** {besitos} 💋
• **Confianza de Diana:** {trust_level}/100
• **Arquetipo Detectado:** {self._get_user_archetype_display(narrative_state)}

🎭 **Análisis de Personalidad:**
{self._get_personality_analysis(narrative_state, trust_level)}

{self.lucien.EMOJIS['diana']} *[Diana observa desde las sombras]*

"*{first_name} está... {self._get_diana_opinion_narrative(trust_level)}*"

*[Con aire evaluativo]*

"*Pero aún hay... mucho camino por recorrer.*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("📈 Ver Progreso Detallado", callback_data="detailed_progress")],
                [InlineKeyboardButton("🎭 Mi Arquetipo", callback_data="my_archetype")],
                [InlineKeyboardButton("💭 ¿Qué piensa Diana de mí?", callback_data="diana_opinion")],
                [InlineKeyboardButton("🎯 ¿Cómo mejorar?", callback_data="how_to_improve")],
                [InlineKeyboardButton("⬅️ Volver al menú", callback_data="back_to_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                profile_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en _show_profile_narrative: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    # === MÉTODOS AUXILIARES PARA NARRATIVA ===

    def _get_user_archetype_display(self, narrative_state: Any) -> str:
        """Obtiene el arquetipo del usuario para mostrar"""
        
        archetype = getattr(narrative_state, 'primary_archetype', 'undefined')
        
        archetype_names = {
            'explorer': 'El Explorador 🔍',
            'direct': 'El Directo ⚡',
            'romantic': 'El Romántico 💫',
            'analytical': 'El Analítico 🧠',
            'persistent': 'El Persistente 💪',
            'patient': 'El Paciente 🕰️',
            'undefined': 'En evaluación... 🤔'
        }
        
        return archetype_names.get(archetype, 'Misterioso 🎭')

    def _get_personality_analysis(self, narrative_state: Any, trust_level: int) -> str:
        """Genera análisis de personalidad"""
        
        if trust_level < 20:
            return "*Personalidad aún en desarrollo. Diana necesita más datos para un análisis completo.*"
        elif trust_level < 50:
            return "*Muestra signos prometedores de comprensión emocional. Diana está... intrigada.*"
        elif trust_level < 80:
            return "*Demuestra madurez emocional notable. Diana ha comenzado a... confiar.*"
        else:
            return "*Excepcional comprensión de la complejidad humana. Diana está genuinamente impresionada.*"

    def _get_diana_opinion_narrative(self, trust_level: int) -> str:
        """Opinión narrativa de Diana según nivel de confianza"""
        
        if trust_level < 20:
            return "evaluando su potencial"
        elif trust_level < 50:
            return "comenzando a interesarse"
        elif trust_level < 80:
            return "genuinamente intrigada"
        else:
            return "profundamente fascinada"

    async def _send_error_message_narrative(self, update: Update) -> None:
        """Mensaje de error con narrativa"""
        
        error_message = self.lucien.get_error_message("narrativa")
        
        try:
            await update.callback_query.edit_message_text(
                error_message, 
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error enviando mensaje de error narrativo: {e}")

    async def _handle_unknown_callback_narrative(self, update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> None:
        """Maneja callbacks desconocidos con narrativa"""
        
        unknown_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con exasperación elegante]*

"*Oh, qué sorpresa... {callback_data} no está implementado yet.*"

*[Con sarcasmo profesional]*

"*Diana me pide que te informe que esa funcionalidad está... en desarrollo.*"

*[Con aire condescendiente]*

"*Mientras tanto, perhaps try something that actually works?*"
        """.strip()

        keyboard = [
            [InlineKeyboardButton("🔙 Volver al menú", callback_data="back_to_menu")],
            [InlineKeyboardButton("🎭 Continuar historia", callback_data="user_main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            unknown_message, 
            reply_markup=reply_markup, 
            parse_mode="Markdown"
        )

    # === CALLBACKS NARRATIVOS FALTANTES ===

    async def _handle_narrative_progress(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Maneja 'narrative_progress'"""

        progress_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire de evaluador]*

"*Tu progreso narrativo... veamos...*"

📊 **Estado Actual:**
• Nivel: Principiante
• Escenas completadas: 1/10
• Comprensión de Diana: 15%

*[Con sarcasmo]*

"*Básicamente... acabas de empezar.*"
        """.strip()

        keyboard = [
            [InlineKeyboardButton("⬅️ Volver", callback_data="back_to_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            progress_message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    async def _handle_continue_story(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Maneja 'continue_story'"""

        story_message = f"""
{self.lucien.EMOJIS['diana']} *[Diana aparece con misterio]*

"*¿Listo para continuar nuestra historia?*"

*[Con aire seductor]*

"*Cada paso que das me revela más sobre ti...*"
        """.strip()

        keyboard = [
            [InlineKeyboardButton("🚪 Descubrir más", callback_data="level1_scene2")],
            [InlineKeyboardButton("⬅️ Volver", callback_data="back_to_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            story_message,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    # === MÉTODOS FALTANTES - AGREGAR AL FINAL DE LA CLASE ===

    async def _handle_missions_original(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Maneja el callback 'missions' del sistema original"""

        try:
            first_name = getattr(user, 'first_name', 'Usuario')

            missions_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire de supervisor reluctante]*

"*Oh, {first_name}... quieres ver tus 'misiones'. Qué... ambicioso.*"

*[Consultando una lista elegante]*

🎯 **Misiones Disponibles:**

🌅 **Misión Diaria**
• Interactuar con Diana hoy
• Recompensa: 10 Besitos 💋
• Estado: Disponible

🎭 **Conocer a Diana**
• Explorar todas las introducciones
• Recompensa: 25 Besitos + Acceso especial
• Estado: En progreso

💎 **Camino al VIP**
• Completar 5 misiones principales
• Recompensa: Token VIP gratuito
• Estado: 0/5

{self.lucien.EMOJIS['diana']} *[Diana susurra desde las sombras]*

"*Cada misión completada me acerca más a ti, {first_name}...*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("✅ Completar Diaria", callback_data="complete_daily")],
                [InlineKeyboardButton("🎭 Explorar Introducciones", callback_data="intro_diana")],
                [InlineKeyboardButton("🔄 Actualizar Progreso", callback_data="refresh_missions")],
                [InlineKeyboardButton("⬅️ Volver al Menú", callback_data="back_to_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                missions_message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_missions_original: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _handle_premium_original(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: Any, narrative_state: Any) -> None:
        """Maneja el callback 'premium' del sistema original"""

        try:
            first_name = getattr(user, 'first_name', 'Usuario')

            premium_message = f"""
{self.lucien.EMOJIS['diana']} *[Diana aparece con aire exclusivo]*

"*{first_name}... quieres ver mi contenido más... íntimo.*"

*[Con sonrisa seductora]*

"*No todo lo que creo está disponible para todos. Las mejores piezas, las más personales... requieren verdadera dedicación.*"

💎 **Contenido Premium Disponible:**

📸 **Fotos Exclusivas**
• Sesión "Elegancia Nocturna"
• Precio: 50 Besitos 💋
• Estado: Disponible

🎥 **Videos Personalizados**
• Saludo con tu nombre
• Precio: 100 Besitos 💋
• Estado: Disponible

✨ **Experiencias VIP**
• Chat privado 30 min
• Precio: 200 Besitos 💋
• Estado: Solo VIP

{self.lucien.EMOJIS['lucien']} *[Con aire profesional]*

"*Los precios reflejan la exclusividad, {first_name}.*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("👑 Obtener Acceso VIP", callback_data="get_vip")],
                [InlineKeyboardButton("📸 Vista Previa", callback_data="vip_preview")],
                [InlineKeyboardButton("💬 Testimonios", callback_data="testimonials")],
                [InlineKeyboardButton("💰 ¿Cómo ganar besitos?", callback_data="earn_besitos")],
                [InlineKeyboardButton("⬅️ Volver al Menú", callback_data="back_to_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                premium_message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_premium_original: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    # === MÉTODOS DE ADMINISTRACIÓN ===

    async def _show_admin_panel(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Any,
        narrative_state: Any,
    ) -> None:
        """Muestra panel de administración"""

        try:
            user_telegram_id = update.effective_user.id
            first_name = getattr(user, "first_name", "Usuario")

            if not self.admin_service.is_admin(user_telegram_id):
                await self._send_no_admin_access_message(update, first_name)
                return

            admin = self.admin_service.get_admin(user_telegram_id)
            admin_stats = self.admin_service.get_admin_statistics(user_telegram_id)

            admin_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire de autoridad]*

"*Ah, {first_name}... bienvenido al centro de control.*"

👑 **Panel de Administración**

**Tu información:**
• Nivel: {admin.admin_level.value.title()}
• Comandos usados: {admin_stats['activity']['total_commands']}
• Última actividad: {admin.last_activity.strftime('%d/%m/%Y %H:%M') if admin.last_activity else 'N/A'}

**Permisos disponibles:**
{self._format_admin_permissions(admin)}

*[Con aire profesional]*

"*¿Qué deseas administrar hoy?*"
            """.strip()

            keyboard = []
            if admin.can_generate_vip_tokens:
                keyboard.append([InlineKeyboardButton("🎫 Generar Token VIP", callback_data="generate_vip_token")])
            if admin.can_manage_channels:
                keyboard.append([InlineKeyboardButton("📺 Gestionar Canales", callback_data="manage_channels")])
            if admin.can_access_analytics:
                keyboard.append([InlineKeyboardButton("📊 Ver Analytics", callback_data="admin_analytics")])
            if admin.can_manage_users:
                keyboard.append([InlineKeyboardButton("👥 Gestionar Usuarios", callback_data="manage_users")])
            if admin.can_manage_admins:
                keyboard.append([InlineKeyboardButton("👑 Gestionar Admins", callback_data="manage_admins")])

            keyboard.append([InlineKeyboardButton("📋 Mi Actividad", callback_data="admin_my_activity")])
            keyboard.append([InlineKeyboardButton("⬅️ Volver al Menú", callback_data="back_to_menu")])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                admin_message,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"❌ Error en _show_admin_panel: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _handle_generate_vip_token(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Any,
        narrative_state: Any,
    ) -> None:
        """Maneja la generación de tokens VIP"""

        try:
            user_telegram_id = update.effective_user.id
            first_name = getattr(user, 'first_name', 'Usuario')

            if not self.admin_service.has_permission(
                user_telegram_id, AdminPermission.GENERATE_VIP_TOKENS
            ):
                await self._send_no_permission_message_admin(update, first_name, "generar tokens VIP")
                return

            can_generate = self.admin_service.can_perform_action(
                user_telegram_id, "generate_vip_token"
            )
            if not can_generate["allowed"]:
                await self._send_limit_reached_message(update, first_name, can_generate["reason"])
                return

            token_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire de autoridad]*

"*{first_name}, vas a generar un token VIP.*"

🎫 **Generador de Tokens VIP**

*[Con aire profesional]*

"*Selecciona el tipo de token que deseas crear:*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("⚡ Token Rápido (24h)", callback_data="admin_token_quick")],
                [InlineKeyboardButton("📅 Token Semanal (7 días)", callback_data="admin_token_weekly")],
                [InlineKeyboardButton("⬅️ Volver al Panel", callback_data="admin_panel")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                token_message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_generate_vip_token: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _handle_manage_channels(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Any,
        narrative_state: Any,
    ) -> None:
        """Maneja la gestión de canales"""

        try:
            user_telegram_id = update.effective_user.id
            first_name = getattr(user, "first_name", "Usuario")

            if not self.admin_service.has_permission(
                user_telegram_id, AdminPermission.MANAGE_CHANNELS
            ):
                await self._send_no_permission_message_admin(update, first_name, "gestionar canales")
                return

            channels_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire de supervisor]*

"*{first_name}, aquí tienes el control de los canales.*"

📺 **Gestión de Canales**

**Canales activos:**
• Canal Gratuito: Los Kinkys
• Canal VIP: El Diván
• Solicitudes pendientes: [Número]

*[Con aire eficiente]*

"*¿Qué deseas hacer?*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("📋 Ver Solicitudes Pendientes", callback_data="admin_pending_requests")],
                [InlineKeyboardButton("✅ Aprobar Solicitudes", callback_data="admin_approve_requests")],
                [InlineKeyboardButton("❌ Rechazar Solicitudes", callback_data="admin_reject_requests")],
                [InlineKeyboardButton("📊 Estadísticas de Canales", callback_data="admin_channel_stats")],
                [InlineKeyboardButton("⚙️ Configurar Auto-aprobación", callback_data="admin_auto_approval")],
                [InlineKeyboardButton("⬅️ Volver al Panel", callback_data="admin_panel")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                channels_message,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_manage_channels: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _handle_admin_analytics(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Any,
        narrative_state: Any,
    ) -> None:
        """Muestra analytics para administradores"""

        try:
            user_telegram_id = update.effective_user.id
            first_name = getattr(user, "first_name", "Usuario")

            if not self.admin_service.has_permission(
                user_telegram_id, AdminPermission.ACCESS_ANALYTICS
            ):
                await self._send_no_permission_message_admin(update, first_name, "acceder a analytics")
                return

            analytics_message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire analítico]*

"*{first_name}, aquí tienes los números que importan.*"

📊 **Analytics del Sistema**

**Usuarios:**
• Total de usuarios: [Número]
• Usuarios activos (7 días): [Número]
• Usuarios VIP: [Número]

**Actividad:**
• Misiones completadas hoy: [Número]
• Tokens VIP generados: [Número]
• Mensajes en canales: [Número]

**Narrativa:**
• Usuarios en Nivel 1: [Número]
• Usuarios en El Diván: [Número]
• Progreso promedio: [Porcentaje]%

*[Con aire profesional]*

"*Los datos nunca mienten.*"
            """.strip()

            keyboard = [
                [InlineKeyboardButton("📈 Analytics Detallados", callback_data="admin_detailed_analytics")],
                [InlineKeyboardButton("👥 Estadísticas de Usuarios", callback_data="admin_user_stats")],
                [InlineKeyboardButton("📺 Estadísticas de Canales", callback_data="admin_channel_analytics")],
                [InlineKeyboardButton("🎯 Estadísticas de Misiones", callback_data="admin_mission_stats")],
                [InlineKeyboardButton("⬅️ Volver al Panel", callback_data="admin_panel")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.callback_query.edit_message_text(
                analytics_message,
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"❌ Error en _handle_admin_analytics: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _handle_manage_admins(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Any,
        narrative_state: Any,
    ) -> None:
        """Placeholder para gestionar administradores"""

        await self._handle_unknown_callback_narrative(update, context, "manage_admins")

    async def _handle_admin_action(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Any,
        narrative_state: Any,
        callback_data: str,
    ) -> None:
        """Maneja acciones específicas de administración"""

        try:
            user_telegram_id = update.effective_user.id
            first_name = getattr(user, "first_name", "Usuario")

            if callback_data == "admin_token_quick":
                await self._generate_quick_vip_token(update, context, user_telegram_id)
            elif callback_data == "admin_token_weekly":
                await self._generate_weekly_vip_token(update, context, user_telegram_id)
            elif callback_data == "admin_my_activity":
                await self._show_admin_activity(update, context, user_telegram_id)
            else:
                await self._handle_unknown_callback_narrative(update, context, callback_data)

        except Exception as e:
            logger.error(f"❌ Error en _handle_admin_action: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    # === MÉTODOS AUXILIARES DE ADMINISTRACIÓN ===

    def _format_admin_permissions(self, admin) -> str:
        """Formatea los permisos del admin para mostrar"""

        permissions = []
        if admin.can_generate_vip_tokens:
            permissions.append("🎫 Generar tokens VIP")
        if admin.can_manage_channels:
            permissions.append("📺 Gestionar canales")
        if admin.can_manage_users:
            permissions.append("👥 Gestionar usuarios")
        if admin.can_access_analytics:
            permissions.append("📊 Ver analytics")
        if admin.can_manage_admins:
            permissions.append("👑 Gestionar admins")
        if admin.can_modify_system:
            permissions.append("⚙️ Configurar sistema")

        return "\n".join(f"• {perm}" for perm in permissions) if permissions else "• Sin permisos especiales"

    async def _send_no_admin_access_message(self, update, first_name: str):
        """Envía mensaje cuando el usuario no es admin"""

        message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire de superioridad]*

"*Oh, {first_name}... qué adorable.*"

*[Con desdén elegante]*

"*¿Realmente creías que podrías acceder al panel de administración?*"

*[Con sarcasmo refinado]*

"*Esto es solo para personas... importantes. Y claramente, tú no lo eres.*"
        """.strip()

        keyboard = [[InlineKeyboardButton("⬅️ Volver al Menú", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    # =========================================================================
    # Callbacks de acciones específicas (Fase 4)
    # =========================================================================

    async def handle_missions_completed(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra misiones completadas del usuario"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            user = self.user_service.get_user_by_telegram_id(user_id)
            if not user:
                await self._send_error_message(update, context, "Usuario no encontrado")
                return

            completed_missions = await self.mission_service.get_user_completed_missions(user_id)

            if not completed_missions:
                missions_text = (
                    f"✅ *Misiones Completadas*\n\n"
                    f"Aún no has completado ninguna misión.\n\n"
                    f"¡Ve al menú de misiones activas para comenzar tu aventura!"
                )

                keyboard = [
                    [InlineKeyboardButton("🎯 Misiones Activas", callback_data="user_missions")],
                    [InlineKeyboardButton("🔙 Menú Principal", callback_data="user_main_menu")],
                ]
            else:
                missions_text = f"✅ *Misiones Completadas* ({len(completed_missions)})\n\n"

                keyboard = []
                for mission in completed_missions[-5:]:
                    missions_text += f"🏆 **{mission.get('title', 'Misión')}**\n"
                    missions_text += f"   Completada: {mission.get('completed_date', 'Fecha desconocida')}\n"
                    missions_text += f"   Recompensa: {mission.get('reward_xp', 0)} XP, {mission.get('reward_besitos', 0)} besitos\n\n"

                keyboard.extend([
                    [InlineKeyboardButton("🎯 Misiones Activas", callback_data="user_missions")],
                    [InlineKeyboardButton("🔙 Menú Principal", callback_data="user_main_menu")],
                ])

            await query.edit_message_text(
                missions_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar misiones completadas: {str(e)}")

    async def handle_missions_refresh(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Actualiza las misiones del usuario - CORREGIDO"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            await query.answer("🔄 Actualizando misiones...")

            new_missions = self.mission_service.generate_personalized_missions(user_id) if hasattr(self.mission_service, 'generate_personalized_missions') else []

            if new_missions:
                refresh_text = (
                    f"🔄 *Misiones Actualizadas*\n\n"
                    f"✨ **Nuevas misiones disponibles:** {len(new_missions)}\n\n"
                    f"Las misiones se han personalizado segun tu progreso y nivel actual.\n\n"
                    f"¡Ve a tus misiones activas para comenzar!"
                )
            else:
                refresh_text = (
                    f"🔄 *Misiones Actualizadas*\n\n"
                    f"📋 No hay nuevas misiones disponibles en este momento.\n\n"
                    f"Completa tus misiones actuales para desbloquear mas contenido."
                )

            keyboard = [
                [InlineKeyboardButton("🎯 Ver Misiones", callback_data="user_missions")],
                [InlineKeyboardButton("🔙 Menu Principal", callback_data="user_main_menu")]
            ]

            await query.edit_message_text(
                refresh_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al actualizar misiones: {str(e)}")

    async def handle_game_trivia_quick(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia trivia rápida"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            await query.answer("🧠 Preparando trivia...")

            trivia_question = await self._generate_trivia_question(user_id)
            if not trivia_question:
                await self._send_error_message(update, context, "No se pudo generar pregunta de trivia")
                return

            context.user_data["current_trivia"] = trivia_question

            question_text = (
                f"🧠 *Trivia Rápida*\n\n"
                f"**Pregunta:**\n{trivia_question['question']}\n\n"
                f"💡 **Pista disponible** (cuesta 10 besitos)\n"
                f"🏆 **Recompensa:** {trivia_question['reward_xp']} XP, {trivia_question['reward_besitos']} besitos"
            )

            keyboard = []
            for i, option in enumerate(trivia_question["options"]):
                keyboard.append([InlineKeyboardButton(f"{chr(65+i)}. {option}", callback_data=f"trivia_answer_{i}")])

            keyboard.extend([
                [InlineKeyboardButton("💡 Pedir Pista", callback_data=f"trivia_hint_{trivia_question['id']}")],
                [InlineKeyboardButton("🔙 Salir", callback_data="user_games")],
            ])

            await query.edit_message_text(
                question_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al iniciar trivia: {str(e)}")

    async def handle_game_number_guess(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia juego de adivinar número"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            await query.answer("🔢 Preparando juego...")

            import random
            target_number = random.randint(1, 100)

            context.user_data["number_game"] = {
                "target": target_number,
                "attempts": 0,
                "max_attempts": 7,
                "min_range": 1,
                "max_range": 100,
            }

            game_text = (
                f"🔢 *Adivina el Número*\n\n"
                f"He pensado en un número entre **1 y 100**.\n\n"
                f"🎯 **Tu misión:** Adivinarlo en máximo 7 intentos\n"
                f"🏆 **Recompensa:** 150 XP + 75 besitos\n"
                f"💡 **Bonus:** Menos intentos = más recompensa\n\n"
                f"**Intentos restantes:** 7\n"
                f"**Rango actual:** 1 - 100\n\n"
                f"Escribe tu número o usa los botones:"
            )

            keyboard = [
                [
                    InlineKeyboardButton("🔢 1-25", callback_data="number_guess_1_25"),
                    InlineKeyboardButton("🔢 26-50", callback_data="number_guess_26_50"),
                ],
                [
                    InlineKeyboardButton("🔢 51-75", callback_data="number_guess_51_75"),
                    InlineKeyboardButton("🔢 76-100", callback_data="number_guess_76_100"),
                ],
                [InlineKeyboardButton("🔙 Salir", callback_data="user_games")],
            ]

            await query.edit_message_text(
                game_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al iniciar juego: {str(e)}")

    async def handle_game_math(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inicia desafío matemático"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            await query.answer("➕ Preparando desafío...")

            math_problem = await self._generate_math_problem(user_id)

            context.user_data["math_game"] = math_problem

            problem_text = (
                f"➕ *Desafío Matemático*\n\n"
                f"**Problema:**\n{math_problem['problem']}\n\n"
                f"⏱️ **Tiempo límite:** 60 segundos\n"
                f"🏆 **Recompensa:** {math_problem['reward_xp']} XP, {math_problem['reward_besitos']} besitos\n\n"
                f"Selecciona tu respuesta:"
            )

            keyboard = []
            for i, option in enumerate(math_problem["options"]):
                keyboard.append([InlineKeyboardButton(f"{option}", callback_data=f"math_answer_{i}")])

            keyboard.append([InlineKeyboardButton("🔙 Salir", callback_data="user_games")])

            await query.edit_message_text(
                problem_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al iniciar desafío matemático: {str(e)}")

    async def _generate_trivia_question(self, user_id: int) -> dict:
        """Genera pregunta de trivia personalizada"""
        try:
            self.user_service.get_user_by_telegram_id(user_id)

            questions_bank = [
                {
                    "id": 1,
                    "question": "¿Cuál es la clave principal de la comunicación efectiva?",
                    "options": ["Hablar mucho", "Escuchar activamente", "Ser gracioso", "Hablar rápido"],
                    "correct": 1,
                    "hint": "La comunicación es bidireccional",
                    "reward_xp": 100,
                    "reward_besitos": 50,
                },
                {
                    "id": 2,
                    "question": "¿Qué porcentaje de la comunicación es lenguaje corporal?",
                    "options": ["25%", "45%", "55%", "75%"],
                    "correct": 2,
                    "hint": "Es más de la mitad",
                    "reward_xp": 120,
                    "reward_besitos": 60,
                },
                {
                    "id": 3,
                    "question": "¿Cuál es el primer paso para generar confianza?",
                    "options": ["Ser vulnerable", "Ser perfecto", "Ser misterioso", "Ser dominante"],
                    "correct": 0,
                    "hint": "Requiere coraje y autenticidad",
                    "reward_xp": 150,
                    "reward_besitos": 75,
                },
            ]

            import random
            return random.choice(questions_bank)

        except Exception as e:
            print(f"Error generating trivia question: {e}")
            return None

    async def _generate_math_problem(self, user_id: int) -> dict:
        """Genera problema matemático personalizado"""
        try:
            user = self.user_service.get_user_by_telegram_id(user_id)

            import random

            # Ajustar dificultad según nivel del usuario
            if user.level <= 2:
                # Nivel básico: sumas y restas simples
                a = random.randint(1, 20)
                b = random.randint(1, 20)
                operation = random.choice(['+', '-'])

                if operation == '+':
                    correct_answer = a + b
                    problem = f"{a} + {b} = ?"
                else:
                    if a < b:  # Evitar negativos
                        a, b = b, a
                    correct_answer = a - b
                    problem = f"{a} - {b} = ?"

            elif user.level <= 5:
                # Nivel intermedio: multiplicación y división
                a = random.randint(2, 12)
                b = random.randint(2, 12)
                operation = random.choice(['*', '/'])

                if operation == '*':
                    correct_answer = a * b
                    problem = f"{a} × {b} = ?"
                else:
                    correct_answer = a
                    a = a * b  # Para que la división sea exacta
                    problem = f"{a} ÷ {b} = ?"

            else:
                # Nivel avanzado: operaciones combinadas
                a = random.randint(5, 15)
                b = random.randint(2, 8)
                c = random.randint(1, 10)

                operations = [
                    (f"({a} + {b}) × {c}", (a + b) * c),
                    (f"{a} × {b} - {c}", a * b - c),
                    (f"{a} + {b} × {c}", a + b * c),
                ]

                problem, correct_answer = random.choice(operations)
                problem += " = ?"

            # Generar opciones incorrectas
            options = [correct_answer]
            while len(options) < 4:
                wrong = correct_answer + random.randint(-10, 10)
                if wrong not in options and wrong > 0:
                    options.append(wrong)

            random.shuffle(options)
            correct_index = options.index(correct_answer)

            return {
                "problem": problem,
                "options": options,
                "correct": correct_index,
                "reward_xp": 80 + (user.level * 20),
                "reward_besitos": 40 + (user.level * 10)
            }

        except Exception as e:
            print(f"Error generating math problem: {e}")
            return {
                "problem": "2 + 2 = ?",
                "options": [4, 3, 5, 6],
                "correct": 0,
                "reward_xp": 50,
                "reward_besitos": 25
            }

    async def handle_trivia_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa respuesta de trivia"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            answer_index = int(query.data.split('_')[-1])

            current_trivia = context.user_data.get('current_trivia')
            if not current_trivia:
                await self._send_error_message(update, context, "No se encontró pregunta activa")
                return

            await query.answer()

            is_correct = answer_index == current_trivia['correct']
            user = self.user_service.get_user_by_telegram_id(user_id)

            if is_correct:
                user.experience += current_trivia['reward_xp']
                user.besitos += current_trivia['reward_besitos']

                level_up = await self._check_level_up(user)

                result_text = (
                    f"🎉 *¡Respuesta Correcta!*\n\n"
                    f"✅ **{current_trivia['options'][answer_index]}** es correcto.\n\n"
                    f"🏆 **Recompensas obtenidas:**\n"
                    f"• +{current_trivia['reward_xp']} XP\n"
                    f"• +{current_trivia['reward_besitos']} besitos\n\n"
                )

                if level_up:
                    result_text += f"🌟 **¡NIVEL SUBIDO!** Ahora eres nivel {user.level}\n\n"

                result_text += (
                    f"📊 **Tu progreso:**\n"
                    f"• Nivel: {user.level}\n"
                    f"• XP: {user.experience}\n"
                    f"• Besitos: {user.besitos}"
                )

            else:
                result_text = (
                    f"❌ *Respuesta Incorrecta*\n\n"
                    f"La respuesta correcta era: **{current_trivia['options'][current_trivia['correct']]}**\n\n"
                    f"💡 **Explicación:** {current_trivia.get('explanation', 'Sigue practicando para mejorar.')}\n\n"
                    f"¡No te desanimes, inténtalo de nuevo!"
                )

            await self.user_service.update_user(user)
            context.user_data.pop('current_trivia', None)

            keyboard = [
                [InlineKeyboardButton("🧠 Nueva Trivia", callback_data="game_trivia_quick")],
                [InlineKeyboardButton("🎮 Otros Juegos", callback_data="user_games")],
                [InlineKeyboardButton("🔙 Menú Principal", callback_data="user_main_menu")]
            ]

            await query.edit_message_text(
                result_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al procesar respuesta: {str(e)}")

    async def handle_math_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa respuesta de desafío matemático"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            answer_index = int(query.data.split('_')[-1])

            math_game = context.user_data.get('math_game')
            if not math_game:
                await self._send_error_message(update, context, "No se encontró desafío activo")
                return

            await query.answer()

            is_correct = answer_index == math_game['correct']
            user = self.user_service.get_user_by_telegram_id(user_id)

            if is_correct:
                user.experience += math_game['reward_xp']
                user.besitos += math_game['reward_besitos']

                level_up = await self._check_level_up(user)

                result_text = (
                    f"🎯 *¡Excelente Cálculo!*\n\n"
                    f"✅ **{math_game['options'][answer_index]}** es correcto.\n\n"
                    f"🏆 **Recompensas:**\n"
                    f"• +{math_game['reward_xp']} XP\n"
                    f"• +{math_game['reward_besitos']} besitos\n\n"
                )

                if level_up:
                    result_text += f"🌟 **¡NIVEL SUBIDO!** Ahora eres nivel {user.level}\n\n"

                result_text += (
                    f"📊 **Estado:** Nivel {user.level} | XP: {user.experience} | Besitos: {user.besitos}"
                )

            else:
                correct_answer = math_game['options'][math_game['correct']]
                result_text = (
                    f"❌ *Intento Fallido*\n\n"
                    f"La respuesta correcta era: **{correct_answer}**\n\n"
                    f"📚 **Consejo:** Practica más operaciones matemáticas básicas.\n\n"
                    f"¡La práctica hace al maestro!"
                )

            await self.user_service.update_user(user)
            context.user_data.pop('math_game', None)

            keyboard = [
                [InlineKeyboardButton("➕ Nuevo Desafío", callback_data="game_math")],
                [InlineKeyboardButton("🎮 Otros Juegos", callback_data="user_games")],
                [InlineKeyboardButton("🔙 Menú Principal", callback_data="user_main_menu")]
            ]

            await query.edit_message_text(
                result_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al procesar desafío: {str(e)}")

    async def _check_level_up(self, user) -> bool:
        """Verifica y procesa subida de nivel"""
        try:
            required_xp = self.user_service.calculate_xp_for_level(user.level + 1)

            if user.experience >= required_xp:
                user.level += 1
                return True

            return False
        except Exception as e:
            print(f"Error checking level up: {e}")
            return False


    # === CALLBACKS DE USUARIO ===

    async def handle_user_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Menú principal dinámico basado en rol de usuario"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            user = self.user_service.get_user_by_telegram_id(user_id)
            if not user:
                await self._send_error_message(update, context, "Usuario no encontrado")
                return

            user_role = self._determine_user_role(user)

            if not hasattr(self, "menu_service"):
                from services.menu_service import MenuService

                self.menu_service = MenuService()

            menu_config = self.menu_service.get_menu_for_user(
                f"main_menu_{user_role}", user_role, user.level
            )

            if menu_config:
                main_menu_text = self._build_dynamic_menu_text(menu_config, user, user_role)
                keyboard = self._build_dynamic_keyboard(menu_config["buttons"])
            else:
                main_menu_text, keyboard = self._build_static_menu(user, user_role)

            # Verificar si es admin para añadir acceso al Diván
            is_admin = False
            try:
                admin = await self.admin_service.get_admin_by_user_id(user_id)
                is_admin = admin and admin.is_active
            except Exception:
                pass

            if is_admin:
                keyboard.append([InlineKeyboardButton("🏛️ Panel de Administración", callback_data="divan_access")])

            await query.edit_message_text(
                main_menu_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar menú principal: {str(e)}")

    def _determine_user_role(self, user) -> str:
        """Determina el rol del usuario"""
        return "vip" if getattr(user, "is_vip", False) else "free"

    def _build_dynamic_menu_text(self, menu_config: Dict, user, user_role: str) -> str:
        """Construye texto del menú dinámicamente"""
        base_text = menu_config["title"] + "\n\n" + menu_config["description"] + "\n\n"

        if user_role == "free":
            base_text += (
                f"📊 **Tu estado (Usuario Gratuito):**\n"
                f"• Nivel: {user.level}\n"
                f"• Besitos: {user.besitos}\n"
                f"• Acceso: 🌟 Básico\n\n"
                f"💡 *¡Únete al canal VIP para desbloquear todo el potencial!*\n\n"
                f"¿Qué deseas hacer?"
            )
        else:
            base_text += (
                f"📊 **Tu estado VIP:**\n"
                f"• Nivel: {user.level}\n"
                f"• Besitos: {user.besitos}\n"
                f"• Acceso: 👑 VIP Premium\n\n"
                f"✨ *Disfruta de todas las funciones exclusivas*\n\n"
                f"¿Qué deseas hacer?"
            )

        return base_text

    def _build_dynamic_keyboard(self, buttons_config: List[Dict]) -> List[List]:
        """Construye teclado dinámicamente"""
        keyboard: List[List] = []
        current_row: List = []
        last_row = -1

        for button in buttons_config:
            if button["row"] != last_row:
                if current_row:
                    keyboard.append(current_row)
                current_row = []
                last_row = button["row"]

            current_row.append(
                InlineKeyboardButton(button["text"], callback_data=button["callback_data"])
            )

        if current_row:
            keyboard.append(current_row)

        return keyboard

    def _build_static_menu(self, user, user_role: str) -> tuple:
        """Menú estático como fallback"""
        if user_role == "free":
            text = (
                f"🎭 *DianaBot - Menú Principal*\n\n"
                f"*Lucien te recibe con elegancia...*\n\n"
                f"\"¡Ah, {user.first_name}! Diana me comentó que podrías venir.\"\n\n"
                f"📊 **Tu estado actual:**\n"
                f"• Nivel: {user.level}\n"
                f"• Besitos: {user.besitos}\n"
                f"• Estado: 🌟 Miembro\n\n"
                f"¿Qué deseas hacer?"
            )

            keyboard = [
                [
                    InlineKeyboardButton("👤 Mi Perfil", callback_data="user_profile"),
                    InlineKeyboardButton("🎯 Misiones", callback_data="user_missions"),
                ],
                [
                    InlineKeyboardButton("🎮 Juegos", callback_data="user_games"),
                    InlineKeyboardButton("🎒 Mochila", callback_data="user_backpack"),
                ],
                [
                    InlineKeyboardButton("🎁 Regalo Diario", callback_data="user_daily_gift"),
                    InlineKeyboardButton("🏆 Ranking", callback_data="user_leaderboard"),
                ],
            ]

            if user.is_vip or user.level >= 5:
                keyboard.append([InlineKeyboardButton("🏆 Subastas VIP", callback_data="user_auctions")])
        else:
            text = (
                f"🎭 *DianaBot - Menú VIP*\n\n"
                f"*Lucien hace una reverencia elegante...*\n\n"
                f"\"¡Ah, {user.first_name}! Diana me comentó que vendrías.\"\n\n"
                f"📊 **Tu estado VIP:**\n"
                f"• Nivel: {user.level}\n"
                f"• Besitos: {user.besitos}\n"
                f"• Estado: 👑 VIP\n\n"
                f"¿Qué deseas hacer?"
            )

            keyboard = [
                [
                    InlineKeyboardButton("👤 Mi Perfil VIP", callback_data="user_profile_vip"),
                    InlineKeyboardButton("🎯 Misiones Premium", callback_data="user_missions_vip"),
                ],
                [
                    InlineKeyboardButton("🎮 Juegos Completos", callback_data="user_games"),
                    InlineKeyboardButton("🎒 Mochila Narrativa", callback_data="user_backpack"),
                ],
                [
                    InlineKeyboardButton("🏆 Subastas VIP", callback_data="user_auctions"),
                    InlineKeyboardButton("🏆 Ranking", callback_data="user_leaderboard"),
                ],
            ]

        return text, keyboard

    async def handle_user_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra el perfil completo del usuario"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            user = self.user_service.get_user_by_telegram_id(user_id)
            if not user:
                await self._send_error_message(update, context, "Usuario no encontrado")
                return

            next_level_xp = self.user_service.calculate_xp_for_level(user.level + 1)
            progress_percentage = (
                (user.experience / next_level_xp) * 100 if next_level_xp > 0 else 100
            )

            profile_text = (
                f"👤 *Perfil de {user.first_name}*\n\n"
                f"📊 **Estadísticas:**\n"
                f"• Nivel: {user.level}\n"
                f"• Experiencia: {user.experience}/{next_level_xp}\n"
                f"• Progreso: {progress_percentage:.1f}%\n"
                f"• Besitos: {user.besitos}\n\n"
                f"🎭 **Estado:**\n"
                f"• Miembro desde: {user.created_at.strftime('%d/%m/%Y')}\n"
                f"• Última actividad: {user.last_activity.strftime('%d/%m/%Y') if user.last_activity else 'Hoy'}\n"
                f"• Estado: {'👑 VIP' if user.is_vip else '🌟 Miembro'}\n\n"
                f"🏆 **Logros:**\n"
                f"• Misiones completadas: 0\n"
                f"• Partidas jugadas: 0\n"
                f"• Días consecutivos: 1"
            )

            keyboard = [
                [
                    InlineKeyboardButton("📊 Estadísticas Detalladas", callback_data="profile_detailed_stats"),
                    InlineKeyboardButton("🎒 Mi Mochila", callback_data="user_backpack"),
                ],
                [
                    InlineKeyboardButton("⚙️ Configuración", callback_data="profile_settings"),
                    InlineKeyboardButton("🏆 Mis Logros", callback_data="profile_achievements"),
                ],
            ]

            if user.is_vip:
                keyboard.append([InlineKeyboardButton("👑 Estado VIP", callback_data="profile_vip_status")])
            else:
                keyboard.append([InlineKeyboardButton("💎 ¿Cómo obtener VIP?", callback_data="profile_vip_info")])

            keyboard.append([InlineKeyboardButton("🔙 Menú Principal", callback_data="user_main_menu")])

            await query.edit_message_text(
                profile_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar perfil: {str(e)}")

    async def handle_profile_detailed_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Estadísticas detalladas del perfil"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            user = self.user_service.get_user_by_telegram_id(user_id)
            if not user:
                await self._send_error_message(update, context, "Usuario no encontrado")
                return

            next_level_xp = self.user_service.calculate_xp_for_level(user.level + 1)
            xp_needed = next_level_xp - user.experience

            detailed_text = (
                f"📊 *Estadísticas Detalladas*\n\n"
                f"👤 **{user.first_name}**\n\n"
                f"🎯 **Progresión:**\n"
                f"• Nivel actual: {user.level}\n"
                f"• XP actual: {user.experience}\n"
                f"• XP para nivel {user.level + 1}: {next_level_xp}\n"
                f"• XP faltante: {xp_needed}\n"
                f"• Progreso: {((user.experience / next_level_xp) * 100):.1f}%\n\n"
                f"💰 **Economía:**\n"
                f"• Besitos: {user.besitos}\n"
                f"• Estado: {'👑 VIP' if user.is_vip else '🌟 Free'}\n\n"
                f"📈 **Actividad:**\n"
                f"• Días activo: 1\n"
                f"• Misiones completadas: 0\n"
                f"• Juegos jugados: 0\n"
                f"• Última conexión: Ahora"
            )

            keyboard = [
                [InlineKeyboardButton("🏆 Ver Logros", callback_data="profile_achievements")],
                [InlineKeyboardButton("📊 Comparar con Otros", callback_data="profile_compare")],
                [InlineKeyboardButton("🔙 Volver al Perfil", callback_data="user_profile")]
            ]

            await query.edit_message_text(
                detailed_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar estadísticas: {str(e)}")

    async def handle_backpack_categories(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra categorías de la mochila"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            categories_text = (
                f"📂 *Categorías de Pistas*\n\n"
                f"🔍 **Organiza tu conocimiento:**\n\n"
                f"🎭 **Seducción** (0 pistas)\n"
                f"   Técnicas y secretos de atracción\n\n"
                f"💬 **Comunicación** (0 pistas)\n"
                f"   Arte de la conversación\n\n"
                f"🧠 **Psicología** (0 pistas)\n"
                f"   Comprende la mente humana\n\n"
                f"🌟 **Desarrollo Personal** (0 pistas)\n"
                f"   Crecimiento y confianza\n\n"
                f"🔮 **Secretos de Diana** (0 pistas)\n"
                f"   Misterios por descubrir"
            )

            keyboard = [
                [
                    InlineKeyboardButton("🎭 Seducción", callback_data="category_seduction"),
                    InlineKeyboardButton("💬 Comunicación", callback_data="category_communication"),
                ],
                [
                    InlineKeyboardButton("🧠 Psicología", callback_data="category_psychology"),
                    InlineKeyboardButton("🌟 Desarrollo", callback_data="category_development"),
                ],
                [InlineKeyboardButton("🔮 Secretos", callback_data="category_secrets")],
                [InlineKeyboardButton("🔙 Volver a Mochila", callback_data="user_backpack")],
            ]

            await query.edit_message_text(
                categories_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar categorías: {str(e)}")

    async def handle_backpack_combine(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Sistema de combinación de pistas"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            combine_text = (
                f"🔄 *Combinar Pistas*\n\n"
                f"🧩 **Alquimia del Conocimiento:**\n\n"
                f"Combina pistas relacionadas para desbloquear secretos más profundos.\n\n"
                f"📋 **Tus combinaciones disponibles:**\n"
                f"• No tienes suficientes pistas para combinar\n\n"
                f"💡 **Consejo:**\n"
                f"Completa más misiones para obtener pistas que puedas combinar.\n\n"
                f"🎯 **Próximo objetivo:**\n"
                f"Obtén al menos 3 pistas de la misma categoría."
            )

            keyboard = [
                [InlineKeyboardButton("🔍 Ver Mis Pistas", callback_data="backpack_view_clues")],
                [InlineKeyboardButton("📂 Categorías", callback_data="backpack_categories")],
                [InlineKeyboardButton("🔙 Volver a Mochila", callback_data="user_backpack")],
            ]

            await query.edit_message_text(
                combine_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar combinaciones: {str(e)}")

    async def handle_category_communication(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra pistas de la categoría Comunicación"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            category_text = (
                f"💬 *Categoria: Comunicacion*\n\n"
                f"🎯 **El Arte de la Conversacion**\n\n"
                f"Aqui encontraras secretos sobre:\n"
                f"• Tecnicas de conversacion\n"
                f"• Lenguaje corporal\n"
                f"• Escucha activa\n"
                f"• Creacion de conexion\n\n"
                f"📋 **Tus pistas de comunicacion:**\n"
                f"• Aun no tienes pistas en esta categoria\n\n"
                f"💡 **Consejo:**\n"
                f"Completa misiones relacionadas con comunicacion para desbloquear pistas."
            )

            keyboard = [
                [InlineKeyboardButton("🔍 Buscar Pistas", callback_data="search_communication_clues")],
                [InlineKeyboardButton("📚 Guia de Comunicacion", callback_data="communication_guide")],
                [InlineKeyboardButton("🔙 Volver a Categorias", callback_data="backpack_categories")]
            ]

            await query.edit_message_text(
                category_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar categoria: {str(e)}")

    async def handle_category_development(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Categoría Desarrollo Personal"""
        query = update.callback_query

        try:
            category_text = (
                f"🌟 *Categoria: Desarrollo Personal*\n\n"
                f"🚀 **Crecimiento y Transformacion**\n\n"
                f"Descubre secretos sobre:\n"
                f"• Autoconfianza y autoestima\n"
                f"• Inteligencia emocional\n"
                f"• Liderazgo personal\n"
                f"• Mentalidad de crecimiento\n\n"
                f"📋 **Tus pistas de desarrollo:**\n"
                f"• Aun no tienes pistas en esta categoria\n\n"
                f"💡 **Consejo:**\n"
                f"El desarrollo personal es la base de toda seduccion autentica."
            )

            keyboard = [
                [InlineKeyboardButton("🔍 Buscar Pistas", callback_data="search_development_clues")],
                [InlineKeyboardButton("📚 Guia de Desarrollo", callback_data="development_guide")],
                [InlineKeyboardButton("🔙 Volver a Categorias", callback_data="backpack_categories")]
            ]

            await query.edit_message_text(
                category_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar categoria: {str(e)}")

    async def handle_category_seduction(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Categoría Seducción"""
        query = update.callback_query

        try:
            category_text = (
                f"🎭 *Categoria: Seduccion*\n\n"
                f"🔥 **El Arte de la Atraccion**\n\n"
                f"Los secretos mas profundos sobre:\n"
                f"• Tecnicas de seduccion avanzadas\n"
                f"• Creacion de tension sexual\n"
                f"• Juegos de poder y control\n"
                f"• Psicologia de la atraccion\n\n"
                f"📋 **Tus pistas de seduccion:**\n"
                f"• Aun no tienes pistas en esta categoria\n\n"
                f"🔮 **Secreto de Diana:**\n"
                f"La verdadera seduccion comienza en la mente."
            )

            keyboard = [
                [InlineKeyboardButton("🔍 Buscar Pistas", callback_data="search_seduction_clues")],
                [InlineKeyboardButton("📚 Manual de Seduccion", callback_data="seduction_manual")],
                [InlineKeyboardButton("🔙 Volver a Categorias", callback_data="backpack_categories")]
            ]

            await query.edit_message_text(
                category_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar categoria: {str(e)}")

    async def handle_back_to_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Regresa al menú principal"""
        await self.handle_user_main_menu(update, context)

    async def handle_user_missions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Menú de misiones del usuario"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            user = self.user_service.get_user_by_telegram_id(user_id)
            if not user:
                await self._send_error_message(update, context, "Usuario no encontrado")
                return

            active_missions = (
                self.mission_service.get_user_active_missions(user_id)
                if hasattr(self.mission_service, "get_user_active_missions")
                else []
            )
            completed_count = (
                self.mission_service.get_user_completed_missions_count(user_id)
                if hasattr(self.mission_service, "get_user_completed_missions_count")
                else 0
            )

            missions_text = "🎯 *Tus Misiones*\n\n"
            missions_text += "📊 **Progreso:**\n"
            missions_text += f"• Activas: {len(active_missions)}\n"
            missions_text += f"• Completadas: {completed_count}\n"
            missions_text += f"• Nivel actual: {user.level}\n\n"

            keyboard = []

            if active_missions:
                missions_text += "🔥 **Misiones Activas:**\n"
                for i, mission in enumerate(active_missions[:3]):
                    missions_text += f"{i+1}. {mission.get('title', 'Misión sin título')}\n"
                    keyboard.append([
                        InlineKeyboardButton(
                            f"📋 {mission.get('title', 'Ver misión')}",
                            callback_data=f"mission_detail_{mission.get('id', i)}",
                        )
                    ])
            else:
                missions_text += "💤 No tienes misiones activas.\n"

            keyboard.extend(
                [
                    [
                        InlineKeyboardButton("✅ Completadas", callback_data="missions_completed"),
                        InlineKeyboardButton("🔄 Actualizar", callback_data="missions_refresh"),
                    ],
                    [InlineKeyboardButton("🔙 Menú Principal", callback_data="user_main_menu")],
                ]
            )

            await query.edit_message_text(
                missions_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar misiones: {str(e)}")

    async def handle_user_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Menú de juegos del usuario"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            user = self.user_service.get_user_by_telegram_id(user_id)
            if not user:
                await self._send_error_message(update, context, "Usuario no encontrado")
                return

            keyboard = [
                [InlineKeyboardButton("🧠 Trivia Rápida", callback_data="game_trivia_quick")],
                [InlineKeyboardButton("🔢 Adivina el Número", callback_data="game_number_guess")],
                [InlineKeyboardButton("➕ Desafío Matemático", callback_data="game_math")],
            ]

            if user.level >= 5:
                keyboard.extend(
                    [
                        [InlineKeyboardButton("📊 Mis Estadísticas", callback_data="games_stats")],
                        [InlineKeyboardButton("🏆 Ranking", callback_data="games_leaderboard")],
                    ]
                )

            keyboard.append([InlineKeyboardButton("🔙 Menú Principal", callback_data="user_main_menu")])

            games_text = (
                "🎮 *Centro de Juegos*\n\n"
                "¡Diviértete y gana experiencia!\n\n"
                "🎯 **Tu Progreso:**\n"
                f"• Nivel: {user.level}\n"
                f"• Experiencia: {user.experience}\n"
                f"• Besitos: {user.besitos}\n"
            )

            if user.level >= 5:
                games_text += "\n🌟 **¡Desbloqueaste funciones avanzadas!**"

            games_text += "\n\nSelecciona un juego:"

            await query.edit_message_text(
                games_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar juegos: {str(e)}")

    async def handle_user_backpack(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Menú de mochila del usuario"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            user = self.user_service.get_user_by_telegram_id(user_id)
            if not user:
                await self._send_error_message(update, context, "Usuario no encontrado")
                return

            lore_pieces = self.user_service.get_user_lore_pieces(user_id)

            keyboard = [
                [InlineKeyboardButton("🔍 Ver Pistas", callback_data="backpack_view_clues")],
                [InlineKeyboardButton("📂 Categorías", callback_data="backpack_categories")],
                [InlineKeyboardButton("🔄 Combinar Pistas", callback_data="backpack_combine")],
                [InlineKeyboardButton("📈 Mi Progreso", callback_data="backpack_progress")],
                [InlineKeyboardButton("🔙 Menú Principal", callback_data="user_main_menu")],
            ]

            backpack_text = (
                "🎒 *Tu Mochila Narrativa*\n\n"
                "Aquí guardas todas las pistas y objetos que descubres.\n\n"
                "📊 **Inventario:**\n"
                f"• Pistas totales: {len(lore_pieces)}\n"
                "• Objetos especiales: 0\n"
                f"• Nivel de mochila: {min(user.level, 10)}/10\n\n"
                "Selecciona una opción:"
            )

            await query.edit_message_text(
                backpack_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar mochila: {str(e)}")

    async def handle_backpack_view_clues(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra pistas de la mochila"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            user = self.user_service.get_user_by_telegram_id(user_id)
            lore_pieces = self.user_service.get_user_lore_pieces(user_id)

            if not lore_pieces:
                clues_text = (
                    f"🔍 *Tus Pistas*\n\n"
                    f"📝 Aún no tienes pistas descubiertas.\n\n"
                    f"💡 **Cómo obtener pistas:**\n"
                    f"• Completar misiones\n"
                    f"• Participar en eventos\n"
                    f"• Interactuar con la narrativa\n"
                    f"• Alcanzar nuevos niveles"
                )
            else:
                clues_text = f"🔍 *Tus Pistas* ({len(lore_pieces)})\n\n"

                for i, clue in enumerate(lore_pieces[:5]):
                    clues_text += f"🔹 **{clue.get('title', f'Pista {i+1}')}**\n"
                    clues_text += f"   {clue.get('description', 'Descripción no disponible')[:50]}...\n\n"

                if len(lore_pieces) > 5:
                    clues_text += f"... y {len(lore_pieces) - 5} pistas más\n\n"

            keyboard = [
                [InlineKeyboardButton("📂 Por Categorías", callback_data="backpack_categories")],
                [InlineKeyboardButton("🔄 Combinar Pistas", callback_data="backpack_combine")],
                [InlineKeyboardButton("🔙 Volver a Mochila", callback_data="user_backpack")]
            ]

            await query.edit_message_text(
                clues_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar pistas: {str(e)}")

    async def handle_backpack_progress(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra progreso narrativo del usuario"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            user = self.user_service.get_user_by_telegram_id(user_id)
            lore_pieces = self.user_service.get_user_lore_pieces(user_id)

            progress_text = (
                f"📈 *Tu Progreso Narrativo*\n\n"
                f"👤 **Perfil:**\n"
                f"• Nivel: {user.level}\n"
                f"• Experiencia: {user.experience}\n"
                f"• Arquetipo: {getattr(user, 'archetype', 'No definido')}\n\n"
                f"🎒 **Colección:**\n"
                f"• Pistas totales: {len(lore_pieces)}\n"
                f"• Objetos especiales: 0\n"
                f"• Combinaciones realizadas: 0\n\n"
                f"🎯 **Siguiente objetivo:**\n"
                f"Alcanzar nivel {user.level + 1} para desbloquear nuevas historias."
            )

            keyboard = [
                [InlineKeyboardButton("🎯 Ver Misiones", callback_data="user_missions")],
                [InlineKeyboardButton("🔍 Ver Pistas", callback_data="backpack_view_clues")],
                [InlineKeyboardButton("🔙 Volver a Mochila", callback_data="user_backpack")]
            ]

            await query.edit_message_text(
                progress_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar progreso: {str(e)}")

    async def handle_user_daily_gift(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Regalo diario del usuario"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            user = self.user_service.get_user_by_telegram_id(user_id)
            if not user:
                await self._send_error_message(update, context, "Usuario no encontrado")
                return

            gift_info = self.user_service.calculate_daily_gift(user_id)

            if gift_info["can_claim"]:
                keyboard = [
                    [InlineKeyboardButton("🎁 Reclamar Regalo", callback_data="claim_daily_gift")],
                    [InlineKeyboardButton("🔙 Menú Principal", callback_data="user_main_menu")],
                ]

                gift_text = (
                    "🎁 *Regalo Diario Disponible!*\n\n"
                    "💰 **Recompensa de hoy:**\n"
                    f"• Base: {gift_info.get('base', 0)} besitos\n"
                    f"• Bonus nivel {user.level}: {gift_info.get('bonus', 0)} besitos\n"
                )

                if gift_info.get("multiplier", 1) > 1:
                    gift_text += f"• Multiplicador VIP: x{gift_info['multiplier']}\n"

                gift_text += f"\n💎 **Total: {gift_info['besitos']} besitos**\n\n¡Haz clic para reclamar!"
            else:
                from datetime import datetime

                hours_until_reset = 24 - datetime.now().hour
                keyboard = [[InlineKeyboardButton("🔙 Menú Principal", callback_data="user_main_menu")]]

                gift_text = (
                    "🎁 *Regalo Diario*\n\n"
                    "✅ **Ya reclamaste tu regalo de hoy!**\n\n"
                    f"⏰ Próximo regalo disponible en: ~{hours_until_reset} horas\n\n"
                    f"💰 Besitos actuales: {user.besitos}"
                )

            await query.edit_message_text(
                gift_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar regalo diario: {str(e)}")

    async def handle_claim_daily_gift(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa la reclamación del regalo diario - CORREGIDO"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            await query.answer("🎁 Procesando regalo...")

            # Calcular regalo antes de otorgarlo
            gift_info = self.user_service.calculate_daily_gift(user_id)

            if not gift_info.get("can_claim", False):
                await self._send_error_message(update, context, "No puedes reclamar el regalo en este momento")
                return

            # Intentar otorgar el regalo
            success = await self.user_service.give_daily_gift(user_id)

            if success:
                # Obtener información actualizada del usuario
                user = self.user_service.get_user_by_telegram_id(user_id)

                success_text = (
                    f"🎉 *¡Regalo Reclamado!*\n\n"
                    f"💰 **Has recibido:** {gift_info.get('besitos', 0)} besitos\n\n"
                    f"📊 **Desglose:**\n"
                    f"• Base: {gift_info.get('base', 0)} besitos\n"
                    f"• Bonus nivel {user.level}: {gift_info.get('bonus', 0)} besitos\n"
                )

                if gift_info.get('multiplier', 1) > 1:
                    success_text += f"• Multiplicador VIP: x{gift_info['multiplier']}\n"

                success_text += (
                    f"\n📊 **Tu estado actual:**\n"
                    f"• Besitos totales: {user.besitos}\n"
                    f"• Nivel: {user.level}\n"
                    f"• Experiencia: {user.experience}"
                )

                keyboard = [
                    [InlineKeyboardButton("🎮 Ir a Juegos", callback_data="user_games")],
                    [InlineKeyboardButton("🎯 Ver Misiones", callback_data="user_missions")],
                    [InlineKeyboardButton("🔙 Menú Principal", callback_data="user_main_menu")],
                ]
            else:
                success_text = (
                    f"❌ *Error al Reclamar Regalo*\n\n"
                    f"No se pudo procesar tu regalo diario.\n"
                    f"Posibles causas:\n"
                    f"• Ya lo reclamaste hoy\n"
                    f"• Error temporal del sistema\n\n"
                    f"Inténtalo de nuevo más tarde."
                )

                keyboard = [
                    [InlineKeyboardButton("🔄 Intentar de Nuevo", callback_data="user_daily_gift")],
                    [InlineKeyboardButton("🔙 Menú Principal", callback_data="user_main_menu")],
                ]

            await query.edit_message_text(
                success_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al reclamar regalo: {str(e)}")

    async def handle_user_leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ranking de usuarios - CORREGIDO CON ANONIMIZACIÓN"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            user = self.user_service.get_user_by_telegram_id(user_id)
            if not user:
                await self._send_error_message(update, context, "Usuario no encontrado")
                return

            top_users = self.user_service.get_top_users_by_level(10) if hasattr(self.user_service, 'get_top_users_by_level') else []
            user_position = self.user_service.get_user_ranking_position(user_id) if hasattr(self.user_service, 'get_user_ranking_position') else 1

            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")

            leaderboard_text = f"🏆 *Ranking Global* (Actualizado: {timestamp})\n\n"

            for i, top_user in enumerate(top_users):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."

                if top_user.telegram_id == user_id:
                    display_name = f"**{top_user.first_name}** 👈 TU"
                else:
                    first_letter = top_user.first_name[0] if top_user.first_name else "U"
                    name_length = len(top_user.first_name) if top_user.first_name else 4
                    asterisks = "*" * max(1, name_length - 1)
                    display_name = f"{first_letter}{asterisks}"

                leaderboard_text += f"{medal} {display_name} - Nivel {top_user.level}\n"

            next_level_xp = self.user_service.calculate_xp_for_level(user.level + 1)
            xp_needed = next_level_xp - user.experience

            leaderboard_text += f"\n📍 **Tu posicion:** #{user_position}\n"
            leaderboard_text += f"🎯 **Tu nivel:** {user.level}\n"
            leaderboard_text += f"⭐ **Tu experiencia:** {user.experience}\n"
            leaderboard_text += f"🚀 **XP para nivel {user.level + 1}:** {xp_needed}"

            keyboard = [
                [
                    InlineKeyboardButton("🔄 Actualizar", callback_data="user_leaderboard"),
                    InlineKeyboardButton("📊 Mi Progreso", callback_data="user_profile")
                ],
                [InlineKeyboardButton("🔙 Menu Principal", callback_data="user_main_menu")]
            ]

            await query.edit_message_text(
                leaderboard_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar ranking: {str(e)}")

    async def handle_user_auctions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Menú de subastas VIP"""
        query = update.callback_query
        user_id = query.from_user.id

        try:
            user = self.user_service.get_user_by_telegram_id(user_id)
            if not user:
                await self._send_error_message(update, context, "Usuario no encontrado")
                return

            if not user.is_vip and user.level < 5:
                await query.edit_message_text(
                    "🏆 *Subastas VIP*\n\n"
                    "❌ **Acceso Restringido**\n\n"
                    "Las subastas están disponibles para:\n"
                    "• Miembros VIP 👑\n"
                    "• Usuarios nivel 5+ 🌟\n\n"
                    "¡Sigue progresando para desbloquear esta función!",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [InlineKeyboardButton("💎 Obtener VIP", callback_data="profile_vip_info")],
                            [InlineKeyboardButton("🔙 Menú Principal", callback_data="user_main_menu")],
                        ]
                    ),
                )
                return

            active_auctions = self.auction_service.get_active_auctions(user.id)

            keyboard = [
                [InlineKeyboardButton("🏆 Subastas Activas", callback_data="auctions_active")],
                [InlineKeyboardButton("📋 Mis Pujas", callback_data="auctions_my_bids")],
                [InlineKeyboardButton("🏅 Historial", callback_data="auctions_history")],
                [InlineKeyboardButton("ℹ️ Cómo Funciona", callback_data="auctions_help")],
                [InlineKeyboardButton("🔙 Menú Principal", callback_data="user_main_menu")],
            ]

            auctions_text = (
                "🏆 *Subastas VIP*\n\n"
                "¡Bienvenido al exclusivo mundo de las subastas!\n\n"
                "📊 **Estado:**\n"
                f"• Subastas activas: {len(active_auctions)}\n"
                f"• Tu nivel: {user.level}\n"
                f"• Besitos disponibles: {user.besitos}\n"
            )

            if user.is_vip:
                auctions_text += "• Estado: 👑 VIP\n"

            auctions_text += "\nSelecciona una opción:"

            await query.edit_message_text(
                auctions_text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

        except Exception as e:
            await self._send_error_message(update, context, f"Error al cargar subastas: {str(e)}")

    async def _send_no_permission_message_admin(self, update, first_name: str, action: str):
        """Mensaje cuando falta permiso"""

        message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire de reproche]*

"*{first_name}, no tienes permiso para {action}.*"
        """.strip()

        keyboard = [[InlineKeyboardButton("⬅️ Volver", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    async def _send_limit_reached_message(self, update, first_name: str, reason: str):
        """Indica que se alcanzó un límite"""

        message = f"""
{self.lucien.EMOJIS['lucien']} *[Con aire de advertencia]*

"*{first_name}, {reason}.*"
        """.strip()

        keyboard = [[InlineKeyboardButton("⬅️ Volver", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    async def _generate_quick_vip_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_telegram_id: int) -> None:
        """Genera un token VIP rápido (24h)"""

        try:
            result = self.admin_service.generate_vip_token(user_telegram_id, "quick")

            if result.get("success"):
                await update.callback_query.edit_message_text(
                    f"🎫 **Token VIP Generado**\n\n"
                    f"Token: `{result['token']}`\n"
                    f"Expira: {result['expiry']}",
                    parse_mode="Markdown"
                )
            else:
                await update.callback_query.edit_message_text(
                    f"❌ Error: {result.get('error', 'Error desconocido')}",
                    parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"❌ Error en _generate_quick_vip_token: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _generate_weekly_vip_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_telegram_id: int) -> None:
        """Genera un token VIP semanal (7 días)"""

        try:
            result = self.admin_service.generate_vip_token(user_telegram_id, "weekly")

            if result.get("success"):
                await update.callback_query.edit_message_text(
                    f"🎫 **Token VIP Generado**\n\n"
                    f"Token: `{result['token']}`\n"
                    f"Expira: {result['expiry']}",
                    parse_mode="Markdown"
                )
            else:
                await update.callback_query.edit_message_text(
                    f"❌ Error: {result.get('error', 'Error desconocido')}",
                    parse_mode="Markdown"
                )

        except Exception as e:
            logger.error(f"❌ Error en _generate_weekly_vip_token: {e}", exc_info=True)
            await self._send_error_message_narrative(update)

    async def _show_admin_activity(self, update, context, telegram_id: int):
        """Muestra actividad del administrador"""

        stats = self.admin_service.get_admin_statistics(telegram_id)
        message = f"""
**Tu actividad**

• Comandos usados: {stats['activity']['total_commands']}
• Último comando: {stats['activity']['last_command'] or 'N/A'}
        """.strip()

        keyboard = [[InlineKeyboardButton("⬅️ Volver", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

