from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus

import config

from ..logging import LOGGER
from Clonify.utils.premium_ui import decorate_caption, decorate_text


class PRO(Client):
    def __init__(self):
        LOGGER(__name__).info("Starting Bot...")
        super().__init__(
            name="Clonify",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            max_concurrent_transmissions=7,
        )

    # ---------------------------------------------------------------
    # Global premium UI layer
    # ---------------------------------------------------------------
    # Every outgoing bot text/caption gets the same quote + random
    # premium custom-emoji treatment. The guard in decorate_text()
    # prevents duplicate decoration during message edits.
    async def send_message(self, *args, **kwargs):
        if len(args) >= 2 and isinstance(args[1], str):
            args = (args[0], decorate_text(args[1], 3), *args[2:])
        elif isinstance(kwargs.get("text"), str):
            kwargs["text"] = decorate_text(kwargs["text"], 3)
        return await super().send_message(*args, **kwargs)

    async def edit_message_text(self, *args, **kwargs):
        if len(args) >= 3 and isinstance(args[2], str):
            args = (args[0], args[1], decorate_text(args[2], 3), *args[3:])
        elif isinstance(kwargs.get("text"), str):
            kwargs["text"] = decorate_text(kwargs["text"], 3)
        return await super().edit_message_text(*args, **kwargs)

    async def send_photo(self, *args, **kwargs):
        if isinstance(kwargs.get("caption"), str):
            kwargs["caption"] = decorate_caption(kwargs["caption"])
        elif len(args) >= 3 and isinstance(args[2], str):
            args = (args[0], args[1], decorate_caption(args[2]), *args[3:])
        return await super().send_photo(*args, **kwargs)

    async def edit_message_caption(self, *args, **kwargs):
        if isinstance(kwargs.get("caption"), str):
            kwargs["caption"] = decorate_caption(kwargs["caption"])
        elif len(args) >= 3 and isinstance(args[2], str):
            args = (args[0], args[1], decorate_caption(args[2]), *args[3:])
        return await super().edit_message_caption(*args, **kwargs)

    async def send_video(self, *args, **kwargs):
        if isinstance(kwargs.get("caption"), str):
            kwargs["caption"] = decorate_caption(kwargs["caption"])
        return await super().send_video(*args, **kwargs)

    async def send_audio(self, *args, **kwargs):
        if isinstance(kwargs.get("caption"), str):
            kwargs["caption"] = decorate_caption(kwargs["caption"])
        return await super().send_audio(*args, **kwargs)

    async def send_document(self, *args, **kwargs):
        if isinstance(kwargs.get("caption"), str):
            kwargs["caption"] = decorate_caption(kwargs["caption"])
        return await super().send_document(*args, **kwargs)

    async def send_animation(self, *args, **kwargs):
        if isinstance(kwargs.get("caption"), str):
            kwargs["caption"] = decorate_caption(kwargs["caption"])
        return await super().send_animation(*args, **kwargs)

    async def send_voice(self, *args, **kwargs):
        if isinstance(kwargs.get("caption"), str):
            kwargs["caption"] = decorate_caption(kwargs["caption"])
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
                text=f"<u><b>» {self.mention} ʙᴏᴛ sᴛᴀʀᴛᴇᴅ :</b></u>\n\nɪᴅ : <code>{self.id}</code>\nɴᴀᴍᴇ : {self.name}\nᴜsᴇʀɴᴀᴍᴇ : @{self.username}",
            )
        except (errors.ChannelInvalid, errors.PeerIdInvalid):
            LOGGER(__name__).error(
                "Bot has failed to access the log group/channel. Make sure that you have added your bot to your log group/channel."
            )
            exit()
        except Exception as ex:
            LOGGER(__name__).error(
                f"Bot has failed to access the log group/channel.\n  Reason : {type(ex).__name__}."
            )
            exit()

        a = await self.get_chat_member(config.LOGGER_ID, self.id)
        if a.status != ChatMemberStatus.ADMINISTRATOR:
            LOGGER(__name__).error(
                "Please promote your bot as an admin in your log group/channel."
            )
            exit()
        LOGGER(__name__).info(f"Music Bot Started as {self.name}")

    async def stop(self):
        await super().stop()
