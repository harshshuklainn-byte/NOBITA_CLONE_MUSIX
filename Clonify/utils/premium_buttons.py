"""Premium button factory for the bot's inline keyboards."""
import random
from typing import Any

from pyrogram.types import InlineKeyboardButton as _InlineKeyboardButton
try:
    from pyrogram.enums import ButtonStyle
except (ImportError, AttributeError):
    ButtonStyle = None

from Clonify.utils.premium_ui import MAIN_EMOJI_ID, PREMIUM_EMOJIS

_ICON_POOL = tuple(str(x) for x in PREMIUM_EMOJIS if str(x).isdigit()) or (MAIN_EMOJI_ID,)


def _button_style(text: str, callback_data: str | None, url: str | None) -> str:
    value = f"{text} {callback_data or ''} {url or ''}".lower()
    if any(x in value for x in ("close", "stop", "cancel", "delete", "remove", "back")):
        return "danger"
    if any(x in value for x in ("play", "resume", "add", "support", "owner", "updates", "next", "skip")):
        return "success"
    return "primary"


def InlineKeyboardButton(text: str, **kwargs: Any):
    """Create a styled button; gracefully fall back on older Pyrogram builds."""
    callback_data = kwargs.get("callback_data")
    url = kwargs.get("url")
    style = kwargs.pop("style", None) or _button_style(text, callback_data, url)
    icon_id = kwargs.pop("icon_custom_emoji_id", None) or random.choice(_ICON_POOL)
    try:
        native_style = getattr(ButtonStyle, style.upper(), style) if ButtonStyle is not None else style
        return _InlineKeyboardButton(text=text, style=native_style, icon_custom_emoji_id=icon_id, **kwargs)
    except (TypeError, AttributeError):
        fallback = {"danger": "🔴", "success": "🟢", "primary": "🔵"}[style]
        return _InlineKeyboardButton(text=f"{fallback} {text}", **kwargs)
