from pathlib import Path

from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus

import config

from ..logging import LOGGER


class PRO(Client):
    def __init__(self):
        LOGGER(__name__).info("Starting Bot...")

        # Keep the Pyrogram bot session on disk.  The old in_memory=True
        # configuration forced a fresh bot authorization after every restart,
        # which contributed to Telegram auth.ImportBotAuthorization FLOOD_WAITs.
        session_dir = Path(".pyrogram_sessions")
        session_dir.mkdir(parents=True, exist_ok=True)

        super().__init__(
            name="Clonify",
            workdir=str(session_dir),
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=False,
            max_concurrent_transmissions=7,
        )

    # ---------------------------------------------------------------
    # Safe premium UI layer
    # ---------------------------------------------------------------
    # Imports are intentionally lazy so the UI package cannot create the
    # Clonify -> utils -> Clonify circular-import problem during startup.
    @staticmethod
    def _decorate_text_safe(text):
        try:
            from Clonify.utils.premium_ui import decorate_text
            return decorate_text(text, 3)
        except Exception as ex:
            LOGGER(__name__).warning(
                f"Premium text decoration skipped: {type(ex).__name__}"
            )
            return text

    @staticmethod
    def _decorate_caption_safe(caption):
        try:
            from Clonify.utils.premium_ui import decorate_caption
            return decorate_caption(caption)
        except Exception as ex:
            LOGGER(__name__).warning(
                f"Premium caption decoration skipped: {type(ex).__name__}"
            )
            return caption

    async def send_message(self, *args, **kwargs):
        if len(args) >= 2 and isinstance(args[1], str):
            args = (args[0], self._decorate_text_safe(args[1]), *args[2:])
        elif isinstance(kwargs.get("text"), str):
            kwargs["text"] = self._decorate_text_safe(kwargs["text"])
        return await super().send_message(*args, **kwargs)

    async def edit_message_text(self, *args, **kwargs):
        if len(args) >= 3 and isinstance(args[2], str):
            args = (args[0], args[1], self._decorate_text_safe(args[2]), *args[3:])
        elif isinstance(kwargs.get("text"), str):
            kwargs["text"] = self._decorate_text_safe(kwargs["text"])
        return await super().edit_message_text(*args, **kwargs)

    async def send_photo(self, *args, **kwargs):
        if isinstance(kwargs.get("caption"), str):
            kwargs["caption"] = self._decorate_caption_safe(kwargs["caption"])
        elif len(args) >= 3 and isinstance(args[2], str):
            args = (args[0], args[1], self._decorate_caption_safe(args[2]), *args[3:])
        return await super().send_photo(*args, **kwargs)

    async def edit_message_caption(self, *args, **kwargs):
        if isinstance(kwargs.get("caption"), str):
            kwargs["caption"] = self._decorate_caption_safe(kwargs["caption"])
        elif len(args) >= 3 and isinstance(args[2], str):
            args = (args[0], args[1], self._decorate_caption_safe(args[2]), *args[3:])
        return await super().edit_message_caption(*args, **kwargs)

    async def send_video(self, *args, **kwargs):
        if isinstance(kwargs.get("caption"), str):
            kwargs["caption"] = self._decorate_caption_safe(kwargs["caption"])
        return await super().send_video(*args, **kwargs)

    async def send_audio(self, *args, **kwargs):
        if isinstance(kwargs.get("caption"), str):
            kwargs["caption"] = self._decorate_caption_safe(kwargs["caption"])
        return await super().send_audio(*args, **kwargs)

    async def send_document(self, *args, **kwargs):
        if isinstance(kwargs.get("caption"), str):
            kwargs["caption"] = self._decorate_caption_safe(kwargs["caption"])
        return await super().send_document(*args, **kwargs)

    async def send_animation(self, *args, **kwargs):
        if isinstance(kwargs.get("caption"), str):
            kwargs["caption"] = self._decorate_caption_safe(kwargs["caption"])
        return await super().send_animation(*args, **kwargs)

    async def send_voice(self, *args, **kwargs):
        if isinstance(kwargs.get("caption"), str):
            kwargs["caption"] = self._decorate_caption_safe(kwargs["caption"])
        return await super().send_voice(*args, **kwargs)

    async def start(self):
        await super().start()

        self.id = self.me.id
        self.name = self.me.first_name + " " + (self.me.last_name or "")
        self.username = self.me.username
        self.mention = self.me.mention

        try:
            await self.send_message(
                chat_id=config.LOGGER_ID,
                text=(
                    f"<u><b>» {self.mention} ʙᴏᴛ sᴛᴀʀᴛᴇᴅ :</b></u>\n\n"
                    f"ɪᴅ : <code>{self.id}</code>\n"
                    f"ɴᴀᴍᴇ : {self.name}\n"
                    f"ᴜsᴇʀɴᴀᴍᴇ : @{self.username}"
                ),
            )
        except (errors.ChannelInvalid, errors.PeerIdInvalid):
            LOGGER(__name__).error(
                "Bot cannot access LOGGER_ID. Add the bot to the log group/channel "
                "and verify LOGGER_ID."
            )
            await super().stop()
            raise
        except Exception as ex:
            LOGGER(__name__).error(
                f"Bot failed to write the startup log: {type(ex).__name__}: {ex}"
            )
            await super().stop()
            raise

        try:
            member = await self.get_chat_member(config.LOGGER_ID, self.id)
        except Exception as ex:
            LOGGER(__name__).error(
                f"Cannot verify bot admin status in LOGGER_ID: "
                f"{type(ex).__name__}: {ex}"
            )
            await super().stop()
            raise

        if member.status != ChatMemberStatus.ADMINISTRATOR:
            LOGGER(__name__).error(
                "Please promote the bot as an administrator in LOGGER_ID."
            )
            await super().stop()
            raise RuntimeError("Bot is not an administrator in LOGGER_ID.")

        LOGGER(__name__).info(f"Music Bot Started as {self.name}")

    async def stop(self):
        if self.is_connected:
            await super().stop()
