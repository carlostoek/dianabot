
    from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from models.user import User
from services.user_service import UserService
from config.settings import settings
from typing import Callable, Any


def user_required(func: Callable) -> Callable:
    """Decorador que garantiza que el usuario esté registrado y carga sus datos"""

    @wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        user_service = UserService()
        telegram_user = update.effective_user

        if not telegram_user:
            await update.message.reply_text(
                "❌ **Error de acceso**\n\n"
                "No se pudo identificar tu usuario. Intenta usar /start primero.",
                parse_mode="Markdown",
            )
            return

        # Obtener o crear usuario
        db_user = user_service.get_or_create_user(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
        )

        # Verificar si está baneado
        if db_user.is_banned:
            await update.message.reply_text(
                "🚫 **Acceso Restringido**\n\n"
                "Tu cuenta ha sido suspendida. Contacta a un administrador si crees que esto es un error.",
                parse_mode="Markdown",
            )
            return

        # Guardar usuario en context para uso posterior
        context.user_data["db_user"] = db_user
        context.user_data["telegram_user"] = telegram_user

        return await func(update, context, *args, **kwargs)

    return wrapper


def admin_required(func: Callable) -> Callable:
    """Decorador que requiere permisos de administrador"""

    @wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        telegram_user = update.effective_user

        if not telegram_user or telegram_user.id not in settings.ADMIN_IDS:
            await update.message.reply_text(
                "🔒 **Acceso Denegado**\n\n"
                "Esta función es solo para administradores.",
                parse_mode="Markdown",
            )
            return

        return await func(update, context, *args, **kwargs)

    return wrapper


def vip_required(func: Callable) -> Callable:
    """Decorador que requiere estatus VIP"""

    @wraps(func)
    @user_required
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        db_user = context.user_data["db_user"]

        if not db_user.is_vip:
            from utils.keyboards import UserKeyboards

            keyboards = UserKeyboards()

            await update.message.reply_text(
                "👑 **Acceso VIP Requerido**\n\n"
                "Esta función es exclusiva para miembros VIP.\n\n"
                "💡 **¿Cómo obtener VIP?**\n"
                "• Participa en subastas\n"
                "• Completa misiones especiales\n"
                "• Mantén una racha alta de actividad\n\n"
                "¡Sigue participando para desbloquear beneficios VIP!",
                reply_markup=keyboards.back_to_menu_keyboard(),
                parse_mode="Markdown",
            )
            return

        return await func(update, context, *args, **kwargs)

    return wrapper


def level_required(min_level: int):
    """Decorador que requiere un nivel mínimo"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @user_required
        async def wrapper(
            update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
        ):
            db_user = context.user_data["db_user"]

            if db_user.level < min_level:
                from utils.keyboards import UserKeyboards

                keyboards = UserKeyboards()

                await update.message.reply_text(
                    f"⭐ **Nivel {min_level} Requerido**\n\n"
                    f"Tu nivel actual: **{db_user.level}**\n"
                    f"Nivel necesario: **{min_level}**\n\n"
                    "💡 **¿Cómo subir de nivel?**\n"
                    "• Completa misiones diarias\n"
                    "• Juega minijuegos\n"
                    "• Participa en trivias\n"
                    "• Reacciona a publicaciones\n\n"
                    "¡Sigue participando para subir de nivel!",
                    reply_markup=keyboards.back_to_menu_keyboard(),
                    parse_mode="Markdown",
                )
                return

            return await func(update, context, *args, **kwargs)

        return wrapper

    return decorator


def rate_limit(max_calls: int = 5, time_window: int = 60):
    """Decorador para limitar la frecuencia de uso de comandos"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
        ):
            user_id = update.effective_user.id
            current_time = int(update.message.date.timestamp())

            # Inicializar rate limiting data si no existe
            if "rate_limit" not in context.user_data:
                context.user_data["rate_limit"] = {}

            func_name = func.__name__
            if func_name not in context.user_data["rate_limit"]:
                context.user_data["rate_limit"][func_name] = []

            # Limpiar llamadas antiguas
            call_times = context.user_data["rate_limit"][func_name]
            call_times[:] = [t for t in call_times if current_time - t < time_window]

            # Verificar límite
            if len(call_times) >= max_calls:
                remaining_time = time_window - (current_time - call_times[0])

                await update.message.reply_text(
                    f"⏰ **Límite de uso alcanzado**\n\n"
                    f"Puedes usar este comando nuevamente en {remaining_time} segundos.\n\n"
                    "💡 **Tip:** Esto ayuda a mantener el bot funcionando bien para todos.",
                    parse_mode="Markdown",
                )
                return

            # Registrar la llamada actual
            call_times.append(current_time)

            return await func(update, context, *args, **kwargs)

        return wrapper

    return decorator


def log_user_action(action_type: str):
    """Decorador para registrar acciones del usuario"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
        ):
            # Registrar la acción antes de ejecutar
            user_id = update.effective_user.id if update.effective_user else None

            # Aquí podrías registrar en logs o base de datos
            print(
                f"Action: {action_type} | User: {user_id} | Function: {func.__name__}"
            )

            result = await func(update, context, *args, **kwargs)

            # Registrar resultado si es necesario
            return result

        return wrapper

    return decorator


def handle_errors(func: Callable) -> Callable:
    """Decorador para manejo elegante de errores"""

    @wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        try:
            return await func(update, context, *args, **kwargs)

        except Exception as e:
            # Log del error
            print(f"Error in {func.__name__}: {str(e)}")

            # Mensaje amigable al usuario
            error_message = """
🤖 **¡Oops! Algo salió mal**

Lo siento, hubo un pequeño problema técnico. 

💡 **¿Qué puedes hacer?**
• Intenta de nuevo en unos segundos
• Usa /start para reiniciar
• Contacta a un administrador si persiste

¡Gracias por tu paciencia! 🙏
            """.strip()

            try:
                if update.message:
                    await update.message.reply_text(
                        error_message, parse_mode="Markdown"
                    )
                elif update.callback_query:
                    await update.callback_query.message.reply_text(
                        error_message, parse_mode="Markdown"
                    )
            except:
                pass  # Si no se puede enviar el mensaje de error, fallar silenciosamente

    return wrapper


def typing_action(func: Callable) -> Callable:
    """Decorador que muestra el indicador de 'escribiendo' durante la ejecución"""

    @wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        # Mostrar indicador de escribiendo
        try:
            if update.message:
                await context.bot.send_chat_action(
                    chat_id=update.effective_chat.id, action="typing"
                )
        except:
            pass  # Fallar silenciosamente si no se puede mostrar

        return await func(update, context, *args, **kwargs)

    return wrapper


def maintenance_mode(func: Callable) -> Callable:
    """Decorador para modo de mantenimiento"""

    @wraps(func)
    async def wrapper(
        update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs
    ):
        # Verificar si está en modo mantenimiento (puedes usar una variable global o configuración)
        maintenance_active = getattr(settings, "MAINTENANCE_MODE", False)

        if maintenance_active:
            # Permitir a administradores usar el bot durante mantenimiento
            user_id = update.effective_user.id if update.effective_user else None
            if user_id not in settings.ADMIN_IDS:
                await update.message.reply_text(
                    "🔧 **Modo de Mantenimiento**\n\n"
                    "El bot está siendo actualizado para brindarte una mejor experiencia.\n\n"
                    "⏰ **Tiempo estimado:** 15-30 minutos\n\n"
                    "¡Gracias por tu paciencia! Vuelve pronto para disfrutar de las nuevas funciones. 🚀",
                    parse_mode="Markdown",
                )
                return

        return await func(update, context, *args, **kwargs)

    return wrapper
   