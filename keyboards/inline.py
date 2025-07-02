from aiogram.utils.keyboard import InlineKeyboardBuilder


def mission_accept_kb(mission_id: int) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Aceptar 🎯 esta gloriosa pérdida de tiempo",
        callback_data=f"accept_mission:{mission_id}",
    )
    return builder


def minigame_kb() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="Jugar 🎮", callback_data="play_minigame")
    return builder
