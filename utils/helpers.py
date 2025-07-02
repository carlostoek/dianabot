from models.narrative import LorePiece


def format_backpack(items: list[LorePiece]) -> str:
    if not items:
        return "Tu mochila está vacía."
    lines = [f"{item.title}: {item.description}" for item in items]
    return "\n".join(lines)
