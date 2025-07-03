from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class StartHandler:
    """Handler del comando /start - Integrado con sistema completo"""

    def __init__(self):
        logger.info("🔍 Inicializando StartHandler...")
        
        try:
            logger.info("🔍 Importando UserService...")
            from services.user_service import UserService
            self.user_service = UserService()
            logger.info("✅ UserService inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando UserService: {e}")
            self.user_service = None

        try:
            logger.info("🔍 Importando ChannelService...")
            from services.channel_service import ChannelService
            self.channel_service = ChannelService()
            logger.info("✅ ChannelService inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando ChannelService: {e}")
            self.channel_service = None

        try:
            logger.info("🔍 Importando AdminService...")
            from services.admin_service import AdminService
            self.admin_service = AdminService()
            logger.info("✅ AdminService inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando AdminService: {e}")
            self.admin_service = None

        try:
            logger.info("🔍 Importando LucienVoice...")
            from utils.lucien_voice import LucienVoice
            self.lucien = LucienVoice()
            logger.info("✅ LucienVoice inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando LucienVoice: {e}")
            self.lucien = None

    async def handle_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Comando /start - Integrado con sistema completo"""
        
        logger.info("🔍 Iniciando handle_start...")
        
        try:
            # Verificar que tenemos update válido
            if not update or not update.effective_user:
                logger.error("❌ Update o effective_user es None")
                await self._send_simple_error(update)
                return

            logger.info(f"🔍 Usuario: {update.effective_user.id} - {update.effective_user.first_name}")

            # Verificar servicios
            if not self.user_service:
                logger.error("❌ UserService no disponible")
                await self._send_simple_error(update)
                return

            # Extraer datos del usuario
            logger.info("🔍 Extrayendo datos del usuario...")
            user_data = {
                "telegram_id": update.effective_user.id,
                "username": update.effective_user.username,
                "first_name": update.effective_user.first_name or "Usuario",
                "last_name": update.effective_user.last_name,
            }
            logger.info(f"✅ Datos extraídos: {user_data}")

            # Verificar si es token VIP
            if context.args and len(context.args) > 0:
                logger.info(f"🔍 Args detectados: {context.args}")
                if context.args[0].startswith("vip_token_"):
                    token = context.args[0].replace("vip_token_", "")
                    logger.info(f"🔍 Token VIP detectado: {token}")
                    await self._handle_vip_token(update, context, user_data, token)
                    return

            # Crear o obtener usuario
            logger.info("🔍 Creando/obteniendo usuario...")
            user = self.user_service.get_or_create_user(user_data)
            logger.info(f"✅ Usuario obtenido: {user}")

            # Verificar si es administrador
            is_admin = False
            if self.admin_service:
                try:
                    admin = await self.admin_service.get_admin_by_user_id(user.telegram_id)
                    is_admin = admin and admin.is_active
                    logger.info(f"🔍 Es administrador: {is_admin}")
                except Exception as e:
                    logger.error(f"❌ Error verificando admin: {e}")

            # Verificar si es usuario nuevo
            from datetime import datetime, date
            today = date.today()
            is_new = user.created_at.date() == today
            logger.info(f"🔍 Usuario nuevo: {is_new}")

            if is_new:
                logger.info("🔍 Enviando experiencia de usuario nuevo...")
                await self._send_new_user_experience(update, context, user, is_admin)
            else:
                logger.info("🔍 Enviando experiencia de usuario recurrente...")
                await self._send_returning_user_experience(update, context, user, is_admin)

            logger.info("✅ handle_start completado exitosamente")

        except Exception as e:
            logger.error(f"❌ Error en handle_start: {e}", exc_info=True)
            await self._send_simple_error(update)

    async def _send_new_user_experience(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Any,
        is_admin: bool = False,
    ) -> None:
        """Experiencia para usuarios nuevos - ACTUALIZADA"""
        
        logger.info("🔍 Iniciando _send_new_user_experience...")
        
        try:
            first_name = getattr(user, 'first_name', 'Usuario')
            logger.info(f"🔍 Nombre: {first_name}")

            # Mensaje de bienvenida narrativo
            welcome_message = f"""🎭 *¡Bienvenido a DianaBot, {first_name}!*

*Lucien susurra con elegancia...*

"Ah, un nuevo invitado. Diana me ha hablado de ti... 
Dice que tienes potencial para algo... especial."

🌟 **Tu viaje comienza aquí:**
• Descubre los secretos de la seducción
• Completa misiones personalizadas  
• Desbloquea tu verdadero potencial
• Únete a una comunidad exclusiva

*Diana te observa desde las sombras...*

¿Estás listo para comenzar tu transformación?"""

            keyboard = []
            
            # Opciones para usuarios nuevos
            keyboard.extend([
                [InlineKeyboardButton("✨ Conocer a Diana", callback_data="intro_diana")],
                [InlineKeyboardButton("🎭 ¿Quién es Lucien?", callback_data="intro_lucien")],
                [InlineKeyboardButton("🚀 Explorar DianaBot", callback_data="intro_bot")]
            ])
            
            # Si es admin, agregar acceso directo
            if is_admin:
                keyboard.append([InlineKeyboardButton("🏛️ Panel de Administración", callback_data="divan_access")])
            
            # Botón para ir directo al menú principal
            keyboard.append([InlineKeyboardButton("🎯 Ir al Menú Principal", callback_data="user_main_menu")])

            reply_markup = InlineKeyboardMarkup(keyboard)

            logger.info("🔍 Enviando mensaje de bienvenida...")
            await update.message.reply_text(
                welcome_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )
            logger.info("✅ Mensaje enviado exitosamente")

        except Exception as e:
            logger.error(f"❌ Error en _send_new_user_experience: {e}", exc_info=True)
            await self._send_simple_error(update)

    async def _send_returning_user_experience(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user: Any,
        is_admin: bool = False,
    ) -> None:
        """Experiencia para usuarios recurrentes - ACTUALIZADA"""
        
        logger.info("🔍 Iniciando _send_returning_user_experience...")
        
        try:
            first_name = getattr(user, 'first_name', 'Usuario')
            level = getattr(user, 'level', 1)
            besitos = getattr(user, 'besitos', 0)
            
            # Mensaje personalizado según el nivel
            if level >= 10:
                status_msg = "Un maestro ha regresado..."
            elif level >= 5:
                status_msg = "Un estudiante avanzado vuelve..."
            else:
                status_msg = "El aprendiz regresa..."

            return_message = f"""🎭 *¡{first_name}, has regresado!*

*Lucien sonríe con complicidad...*

"{status_msg} Diana me comentó que has estado progresando. Interesante..."

📊 **Tu progreso actual:**
• Nivel: {level}
• Besitos: {besitos}
• Estado: {'👑 VIP' if getattr(user, 'is_vip', False) else '🌟 Miembro'}

*Sus ojos brillan con secretos por descubrir...*

¿Qué deseas hacer hoy?"""

            keyboard = []
            
            # Opciones principales para usuarios recurrentes
            keyboard.extend([
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
            ])
            
            # Opciones VIP si aplica
            if getattr(user, 'is_vip', False) or level >= 5:
                keyboard.append([InlineKeyboardButton("🏆 Subastas VIP", callback_data="user_auctions")])
            
            # Si es admin, agregar acceso al panel
            if is_admin:
                keyboard.append([InlineKeyboardButton("🏛️ Acceder al Diván", callback_data="divan_access")])
            
            # Menú principal
            keyboard.append([InlineKeyboardButton("🎭 Menú Principal", callback_data="user_main_menu")])

            reply_markup = InlineKeyboardMarkup(keyboard)

            logger.info("🔍 Enviando mensaje de regreso...")
            await update.message.reply_text(
                return_message, 
                reply_markup=reply_markup, 
                parse_mode="Markdown"
            )
            logger.info("✅ Mensaje enviado exitosamente")

        except Exception as e:
            logger.error(f"❌ Error en _send_returning_user_experience: {e}", exc_info=True)
            await self._send_simple_error(update)

    async def _send_simple_error(self, update: Update) -> None:
        """Envía mensaje de error simple"""
        try:
            if update and update.message:
                error_message = """🎭 *Error Técnico*

*Lucien se disculpa elegantemente...*

"Mis disculpas, ha ocurrido un inconveniente técnico. Diana no estará complacida..."

Por favor intenta de nuevo con /start"""

                keyboard = [[InlineKeyboardButton("🔄 Reintentar", callback_data="user_main_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await update.message.reply_text(
                    error_message,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje de error: {e}")

    async def _handle_vip_token(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_data: Dict,
        token: str,
    ) -> None:
        """Maneja tokens VIP - INTEGRADO CON SISTEMA"""
        
        logger.info(f"🔍 Procesando token VIP: {token}")
        
        try:
            # Crear/obtener usuario primero
            user = self.user_service.get_or_create_user(user_data)
            
            # Validar token VIP
            if self.channel_service:
                is_valid = self.channel_service.validate_vip_token(token)
                
                if is_valid:
                    # Activar VIP
                    success = self.channel_service.activate_vip_membership(user.telegram_id, token)
                    
                    if success:
                        vip_message = f"""🎭 *¡Token VIP Activado!*

*Lucien hace una reverencia elegante...*

"¡Excelente! Diana estará... complacida. Has desbloqueado el acceso VIP."

👑 **Beneficios VIP activados:**
• Acceso a subastas exclusivas
• Misiones premium
• Recompensas multiplicadas
• Contenido narrativo especial
• Soporte prioritario

*Un mundo de secretos se abre ante ti...*

¿Deseas explorar tus nuevos privilegios?"""

                        keyboard = [
                            [InlineKeyboardButton("🏆 Explorar Subastas VIP", callback_data="user_auctions")],
                            [InlineKeyboardButton("👑 Ver Beneficios VIP", callback_data="profile_vip_status")],
                            [InlineKeyboardButton("🎭 Ir al Menú Principal", callback_data="user_main_menu")]
                        ]
                    else:
                        vip_message = "❌ Error al activar membresía VIP. Contacta soporte."
                        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="user_main_menu")]]
                else:
                    vip_message = f"""🎭 *Token VIP Inválido*

*Lucien frunce el ceño...*

"Hmm, este token no parece ser válido. Diana no lo reconoce."

Token: `{token}`

¿Estás seguro de que es correcto?"""
                    
                    keyboard = [
                        [InlineKeyboardButton("💎 ¿Cómo obtener VIP?", callback_data="profile_vip_info")],
                        [InlineKeyboardButton("🔙 Volver", callback_data="user_main_menu")]
                    ]
            else:
                vip_message = "⚠️ Sistema VIP temporalmente no disponible."
                keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="user_main_menu")]]

            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                vip_message,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            logger.info("✅ Respuesta VIP enviada")
            
        except Exception as e:
            logger.error(f"❌ Error en _handle_vip_token: {e}", exc_info=True)
            await self._send_simple_error(update)

    
