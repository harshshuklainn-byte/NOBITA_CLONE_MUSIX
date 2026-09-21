# Install the premium button factory before any utility/plugin module imports
# InlineKeyboardButton, so the entire project receives the same UI layer.
from Clonify.utils.premium_buttons import InlineKeyboardButton as _PremiumInlineKeyboardButton
import pyrogram.types as _pyrogram_types
_pyrogram_types.InlineKeyboardButton = _PremiumInlineKeyboardButton

from .channelplay import *
from .database import *
from .decorators import *
from .extraction import *
from .formatters import *
from .inline import *
from .sys import *
