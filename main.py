from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from handlers.callback_handler_narrative import CallbackHandlerNarrative  # Importar el nuevo handler
from handlers.start_handler import StartHandler

async def main() -> None:
    """Inicia el bot de Telegram."""
    application = ApplicationBuilder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

    # Inicializar handlers
    start_handler = StartHandler()
    callback_handler_narrative = CallbackHandlerNarrative()  # Usar el nuevo handler

    # Comandos
    application.add_handler(CommandHandler("start", start_handler.start))

    # Callbacks
    application.add_handler(CallbackQueryHandler(callback_handler_narrative.handle_callback))

    # Iniciar el bot
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
