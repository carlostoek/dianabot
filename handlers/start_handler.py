from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

class StartHandler:
    def __init__(self):
        self.router = Router()

    def register(self, dp):
        """Registrar handlers"""
        dp.include_router(self.router)
        self.router.message.register(self.handle_start, CommandStart())
        self.router.callback_query.register(self.handle_callback, lambda c: c.data in [
            "discover_more", "user_profile", "explore", "narrative_1_1"
        ])

    async def handle_start(self, message: Message):
        """Manejar comando /start"""
        try:
            user_name = message.from_user.first_name or "Usuario"
            user_id = message.from_user.id
            
            print(f"🎭 Usuario {user_name} ({user_id}) inició el bot")
            
            # Intentar crear/obtener usuario
            try:
                await self.create_or_get_user(message.from_user)
            except Exception as e:
                print(f"⚠️ Error creando usuario: {e}")
            
            welcome_text = f"""🎭 *¡Bienvenido a DianaBot, {user_name}!*

*Diana aparece entre las sombras...*

"Bienvenido a Los Kinkys. Has cruzado una línea que muchos ven... pero pocos realmente atraviesan.

Puedo sentir tu curiosidad desde aquí. Es... intrigante.

No todos llegan con esa misma hambre en los ojos."

💰 **Has recibido 100 besitos de bienvenida**
🎯 **Nivel:** 1
📚 **Narrativa:** Nivel 1

*Sus ojos brillan con secretos por descubrir...*

¿Estás preparado para descubrir más?"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("🚪 Descubrir más", callback_data="discover_more")],
                [InlineKeyboardButton("👤 Mi Perfil", callback_data="user_profile")],
                [InlineKeyboardButton("🎮 Explorar DianaBot", callback_data="explore")]
            ])
            
            await message.answer(
                welcome_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
        except Exception as e:
            print(f"❌ Error en start_handler: {e}")
            import traceback
            traceback.print_exc()
            
            # Mensaje de fallback
            await message.answer(
                f"🎭 ¡Hola {message.from_user.first_name}!\n\n"
                "Bienvenido a DianaBot. El sistema está iniciando...\n\n"
                "Usa /start nuevamente en unos segundos.",
                parse_mode="Markdown"
            )

    async def handle_callback(self, callback: CallbackQuery):
        """Manejar callbacks básicos"""
        try:
            await callback.answer()
            
            user_name = callback.from_user.first_name or "Usuario"
            
            if callback.data == "discover_more":
                response_text = f"""🎭 *Lucien aparece elegantemente...*

🎩 **Lucien:**
"Ah, {user_name}. Permíteme presentarme: Lucien, guardián de los secretos que Diana no cuenta... todavía.

Veo que Diana ya plantó esa semilla de curiosidad en ti. Lo noto en cómo llegaste hasta aquí.

Pero la curiosidad sin acción es solo... voyeurismo pasivo."

*Sus ojos evalúan tu determinación*

"Diana observa. Siempre observa. Y lo que más le fascina no es la obediencia ciega, sino la intención detrás de cada gesto."

🎯 **¿Qué deseas explorar?**"""

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton("📚 Conocer la Historia", callback_data="narrative_1_1")],
                    [InlineKeyboardButton("🎮 Juegos y Desafíos", callback_data="games_menu")],
                    [InlineKeyboardButton("🏪 Tienda de Lucien", callback_data="store_menu")],
                    [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")]
                ])

            elif callback.data == "user_profile":
                response_text = f"""👤 *Perfil de {user_name}*

📊 **Tus Estadísticas:**
• Nivel: 1
• Experiencia: 0/100 XP
• Besitos: 100 💰
• Estado: 🌟 Miembro Free

🎭 **Progreso Narrativo:**
• Nivel actual: Los Kinkys (Nivel 1)
• Escenas completadas: 0
• Arquetipo: Por determinar

🏆 **Logros:**
• Recién llegado ✨
• Primer encuentro con Diana 🎭

*Diana susurra: "Interesante... muy interesante."*"""

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton("📈 Ver Progreso Detallado", callback_data="detailed_progress")],
                    [InlineKeyboardButton("🎒 Mi Mochila", callback_data="user_inventory")],
                    [InlineKeyboardButton("🔙 Menú Principal", callback_data="main_menu")]
                ])

            elif callback.data == "explore":
                response_text = f"""🎮 *Explorar DianaBot*

🌟 **¿Qué puedes hacer aquí?**

📚 **Narrativa Inmersiva:**
• Interactúa con Diana y Lucien
• Descubre secretos ocultos
• Progresa a través de 6 niveles narrativos

🎯 **Gamificación:**
• Gana experiencia y sube de nivel
• Colecciona besitos (moneda del sistema)
• Desbloquea logros y badges

🏪 **Economía:**
• Compra contenido exclusivo
• Participa en subastas VIP
• Gana recompensas por actividad

🎭 **Personalización:**
• El sistema detecta tu arquetipo
• Contenido adaptado a tu personalidad
• Experiencia única para cada usuario"""

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton("🚀 ¡Comenzar Aventura!", callback_data="narrative_1_1")],
                    [InlineKeyboardButton("❓ Más Información", callback_data="more_info")],
                    [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")]
                ])

            else:
                response_text = "🎭 Función en desarrollo..."
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton("🔙 Volver", callback_data="main_menu")]
                ])

            await callback.message.edit_text(
                response_text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )

        except Exception as e:
            print(f"❌ Error en callback: {e}")
            await callback.answer("Error procesando solicitud", show_alert=True)

    async def create_or_get_user(self, telegram_user):
        """Crear o obtener usuario de la base de datos"""
        try:
            from config.database import get_db
            from database.models import User
            
            async for db in get_db():
                # Buscar usuario existente
                from sqlalchemy import select
                result = await db.execute(
                    select(User).where(User.telegram_id == telegram_user.id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    # Crear nuevo usuario
                    user = User(
                        telegram_id=telegram_user.id,
                        username=telegram_user.username,
                        first_name=telegram_user.first_name or "Usuario",
                        last_name=telegram_user.last_name,
                        besitos=100,
                        level=1,
                        narrative_level=1
                    )
                    db.add(user)
                    await db.commit()
                    print(f"✅ Usuario creado: {user.first_name}")
                else:
                    print(f"✅ Usuario existente: {user.first_name}")
                
                return user
                
        except Exception as e:
            print(f"⚠️ Error en base de datos: {e}")
            return None
                
