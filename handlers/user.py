from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from models.user import User, UserStats
from services.user_service import UserService
from utils.keyboards import UserKeyboards
from utils.decorators import user_required
from config.database import get_db
from datetime import datetime, timedelta

user_service = UserService()
keyboards = UserKeyboards()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Registro de usuario"""
    user = update.effective_user

    # Registrar o actualizar usuario
    db_user = user_service.get_or_create_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
    )

    welcome_text = f"""
🌟 ¡Bienvenido/a {user.first_name}! 🌟

¡Te has unido a nuestra comunidad! Aquí podrás:

🎮 Jugar minijuegos y trivias
🎯 Completar misiones épicas
💰 Ganar besitos (nuestra moneda)
🏆 Participar en subastas VIP
🗺️ Descubrir historias secretas
🎁 Reclamar regalos diarios

Tu nivel actual: **{db_user.level}**
Besitos: **{db_user.besitos}** 💋

¡Usa /help para ver todos los comandos!
    """

    keyboard = keyboards.main_menu_keyboard(db_user)

    await update.message.reply_text(
        welcome_text, reply_markup=keyboard, parse_mode="Markdown"
    )


@user_required
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /profile - Mostrar perfil de usuario"""
    user = context.user_data["db_user"]
    stats = user_service.get_user_stats(user.id)

    # Calcular progreso al siguiente nivel
    next_level_xp = user_service.calculate_xp_for_level(user.level + 1)
    progress = min(100, (user.experience / next_level_xp) * 100)

    profile_text = f"""
👤 **Perfil de {user.first_name}**

🆔 ID: `{user.telegram_id}`
⭐ Nivel: **{user.level}**
💋 Besitos: **{user.besitos}**
🎯 Experiencia: {user.experience}/{next_level_xp} ({progress:.1f}%)

📊 **Estadísticas:**
❤️ Reacciones dadas: {stats.total_reactions}
✅ Misiones completadas: {stats.missions_completed}
🎮 Juegos jugados: {stats.games_played}
🧠 Trivias correctas: {stats.trivia_correct}/{stats.trivia_total}
🏆 Subastas ganadas: {stats.auctions_won}

👑 Estado VIP: {'✅ Activo' if user.is_vip else '❌ No activo'}
📅 Registrado: {user.created_at.strftime('%d/%m/%Y')}
    """

    keyboard = keyboards.profile_keyboard()

    await update.message.reply_text(
        profile_text, reply_markup=keyboard, parse_mode="Markdown"
    )


@user_required
async def daily_gift_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /daily - Regalo diario"""
    user = context.user_data["db_user"]

    # Verificar si ya reclamó hoy
    if user.last_daily_claim:
        time_diff = datetime.utcnow() - user.last_daily_claim
        if time_diff < timedelta(days=1):
            remaining = timedelta(days=1) - time_diff
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60

            await update.message.reply_text(
                f"⏰ Ya reclamaste tu regalo diario!\n"
                f"Vuelve en {hours}h {minutes}m para el próximo.",
                reply_markup=keyboards.back_to_menu_keyboard(),
            )
            return

    # Dar regalo diario
    daily_amount = user_service.calculate_daily_gift(user.id)
    user_service.give_daily_gift(user.id, daily_amount)

    gift_text = f"""
🎁 **¡Regalo Diario Reclamado!**

Has recibido **{daily_amount} besitos** 💋

💰 Total de besitos: **{user.besitos + daily_amount}**

¡Vuelve mañana para otro regalo!
    """

    await update.message.reply_text(
        gift_text, reply_markup=keyboards.back_to_menu_keyboard(), parse_mode="Markdown"
    )


@user_required
async def backpack_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /mochila - Mostrar mochila narrativa"""
    user = context.user_data["db_user"]
    lore_pieces = user_service.get_user_lore_pieces(user.id)

    if not lore_pieces:
        await update.message.reply_text(
            "🎒 **Tu mochila está vacía**\n\n"
            "Completa misiones para obtener pistas de la historia!",
            reply_markup=keyboards.back_to_menu_keyboard(),
            parse_mode="Markdown",
        )
        return

    backpack_text = "🎒 **Tu Mochila Narrativa**\n\n"

    for i, piece in enumerate(lore_pieces, 1):
        backpack_text += f"📜 **{i}. {piece.title}**\n"
        backpack_text += f"_{piece.description}_\n\n"

    # Verificar si puede combinar pistas
    combinations = user_service.check_lore_combinations(user.id)
    if combinations:
        backpack_text += "✨ **¡Puedes combinar pistas!**\n"
        backpack_text += "Usa el botón de abajo para descubrir secretos.\n"

    keyboard = keyboards.backpack_keyboard(len(lore_pieces), bool(combinations))

    await update.message.reply_text(
        backpack_text, reply_markup=keyboard, parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help - Ayuda"""
    help_text = """
🤖 **Comandos Disponibles:**

👤 **Usuario:**
/profile - Ver tu perfil y estadísticas
/daily - Reclamar regalo diario
/mochila - Ver tu mochila narrativa

🎮 **Juegos:**
/games - Menú de minijuegos
/trivia - Trivia rápida

🎯 **Misiones:**
/missions - Ver misiones disponibles

🏆 **Subastas:**
/auctions - Ver subastas VIP

👑 **Admin** (solo administradores):
/admin - Panel de administración
/addchannel - Agregar canal
/users - Lista de usuarios

💡 **Tip:** ¡Reacciona a los mensajes para ganar besitos!
    """

    await update.message.reply_text(help_text, parse_mode="Markdown")


async def handle_user_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja callbacks de usuarios"""
    query = update.callback_query
    data = query.data

    if data == "user_main_menu":
        await main_menu_callback(update, context)
    elif data == "user_profile":
        await profile_callback(update, context)
    elif data == "user_daily":
        await daily_callback(update, context)
    elif data == "user_backpack":
        await backpack_callback(update, context)
    elif data == "user_combine_lore":
        await combine_lore_callback(update, context)


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostrar menú principal"""
    query = update.callback_query
    user = context.user_data["db_user"]

    menu_text = f"""
🌟 **Menú Principal** 🌟

¡Hola {user.first_name}!

Nivel: **{user.level}** ⭐
Besitos: **{user.besitos}** 💋
Estado: {'👑 VIP' if user.is_vip else '👤 Normal'}

¿Qué quieres hacer hoy?
    """

    keyboard = keyboards.main_menu_keyboard(user)

    await query.edit_message_text(
        menu_text, reply_markup=keyboard, parse_mode="Markdown"
    )


# Más callbacks y funciones...
   