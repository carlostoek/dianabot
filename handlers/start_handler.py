async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start - SIN BD temporalmente"""
    
    logger.info("🔍 Iniciando handle_start...")
    
    try:
        if not update or not update.effective_user:
            logger.error("❌ Update o effective_user es None")
            await self._send_simple_error(update)
            return

        logger.info(f"🔍 Usuario: {update.effective_user.id} - {update.effective_user.first_name}")

        # TEMPORAL: Simular usuario sin BD
        user_data = {
            "telegram_id": update.effective_user.id,
            "username": update.effective_user.username,
            "first_name": update.effective_user.first_name or "Usuario",
            "last_name": update.effective_user.last_name,
        }

        # SIMULAR usuario nuevo para testing
        logger.info("🔍 Enviando experiencia de usuario nuevo (modo temporal)...")
        await self._send_new_user_experience_simple(update, user_data)

        logger.info("✅ handle_start completado exitosamente (modo temporal)")

    except Exception as e:
        logger.error(f"❌ Error en handle_start: {e}", exc_info=True)
        await self._send_simple_error(update)

async def _send_new_user_experience_simple(self, update: Update, user_data: dict) -> None:
    """Experiencia simple sin BD"""
    
    first_name = user_data.get('first_name', 'Usuario')
    
    welcome_message = f"""
🎭 *¡Bienvenido {first_name}!*

Has llegado al bot de Diana. 

Soy Lucien, su mayordomo personal. Diana está... interesada en conocerte.

*[Modo temporal - Sin base de datos]*

¿Qué te gustaría hacer?
    """.strip()

    keyboard = [
        [InlineKeyboardButton("✨ Conocer a Diana", callback_data="intro_diana")],
        [InlineKeyboardButton("🎭 ¿Quién es Lucien?", callback_data="intro_lucien")],
        [InlineKeyboardButton("🔥 Explorar el bot", callback_data="intro_bot")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_message, 
        reply_markup=reply_markup, 
        parse_mode="Markdown"
    )
    
