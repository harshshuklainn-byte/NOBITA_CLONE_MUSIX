import asyncio
import importlib

from pyrogram import idle
from pyrogram.errors import FloodWait
from pytgcalls.exceptions import NoActiveGroupCall

import config
from Clonify import LOGGER, app, userbot
from Clonify.core.call import PRO
from Clonify.misc import sudo
from Clonify.plugins import ALL_MODULES
from Clonify.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS
from Clonify.plugins.tools.clone import restart_bots


async def _start_with_floodwait(start_callable, label):
    """Start a Telegram client without turning FloodWait into a restart loop."""
    while True:
        try:
            return await start_callable()
        except FloodWait as ex:
            wait_seconds = max(int(getattr(ex, "value", 1)), 1) + 5
            LOGGER("Clonify").warning(
                f"{label}: Telegram FLOOD_WAIT is active. "
                f"Waiting {wait_seconds} seconds before retrying."
            )
            await asyncio.sleep(wait_seconds)


async def init():
    if not config.STRING1:
        LOGGER(__name__).error(
            "String Session not filled, please provide a valid session."
        )
        return

    await sudo()

    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)

        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except Exception as ex:
        LOGGER(__name__).warning(
            f"Ban-list preload skipped: {type(ex).__name__}"
        )

    # IMPORTANT:
    # The old code allowed auth.ImportBotAuthorization FloodWait to escape.
    # The process supervisor then restarted the container every few seconds,
    # causing another authorization attempt and keeping the bot offline.
    await _start_with_floodwait(app.start, "Bot")

    try:
        for all_module in ALL_MODULES:
            importlib.import_module("Clonify.plugins" + all_module)

        LOGGER("Clonify.plugins").info(
            "𝐀𝐥𝐥 𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬 𝐋𝐨𝐚𝐝𝐞𝐝 𝐁𝐚𝐛𝐲🥳..."
        )

        await _start_with_floodwait(userbot.start, "Userbot")
        await PRO.start()

        try:
            await PRO.stream_call(
                "https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4"
            )
        except NoActiveGroupCall:
            LOGGER("Clonify").error(
                "Please start your log group's voice chat/channel first."
            )
            return
        except Exception:
            pass

        await PRO.decorators()
        await restart_bots()

        LOGGER("Clonify").info(
            "╔═════ஜ۩۞۩ஜ════╗\n"
            "  ☠︎︎𝗠𝗔𝗗𝗘 𝗕𝗬 𝗣𝗿𝗼𝗕𝗼t𝘀☠︎︎\n"
            "╚═════ஜ۩۞۩ஜ════╝"
        )

        await idle()

    finally:
        for client, label in (
            (app, "Bot"),
            (userbot, "Userbot"),
        ):
            try:
                if client.is_connected:
                    await client.stop()
            except Exception as ex:
                LOGGER("Clonify").warning(
                    f"{label} shutdown warning: {type(ex).__name__}"
                )


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())
