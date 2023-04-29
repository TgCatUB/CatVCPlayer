import asyncio
import logging

from telethon import Button, TelegramClient
from telethon.sessions import StringSession
from userbot import Config, catub
from userbot.core.managers import edit_or_reply

from .vcp_helper import CatVC

logging.getLogger("pytgcalls").setLevel(logging.ERROR)

if vc_session := Config.VC_SESSION:
    vc_client = TelegramClient(
        StringSession(vc_session), Config.APP_ID, Config.API_HASH
    )
else:
    vc_client = catub

vc_client.__class__.__module__ = "telethon.client.telegramclient"
vc_player = CatVC(vc_client)


@vc_player.app.on_stream_end()
async def handler(_, update):
    event = False
    if not vc_player.PLAYLIST:
        if vc_player.CHAT_ID and not vc_player.SILENT:
            return await vc_player.leave_vc()
        else:
            return
    resp = await vc_player.handle_next(update)
    vcbot = catub.tgbot if vc_player.BOTMODE else catub
    print("In the end it doesnt even matter")
    buttons = [
        [
            Button.inline("⏸ Pause", data="pausevc"),
            Button.inline("▶️ Resume", data="resumevc"),
            Button.inline("🔁 repeat", data="repeatvc"),
        ],
        [
            Button.inline("🪡 Skip", data="skipvc"),
            Button.inline("❌ Stop", data="leavevc"),
        ],
        [
            Button.inline("🗑 close", data="vc_close"),
        ],
    ]
    if resp and type(resp) is list:
        caption = resp[1].split(f"\n\n")[1] if f"\n\n" in resp[1] else resp[1]
        event = await vcbot.send_file(
            vc_player.CHAT_ID, file=resp[0], caption=caption, buttons=buttons
        )
    elif resp and type(resp) is str:
        resp = resp.split(f"\n\n")[1] if f"\n\n" in resp else resp
        event = await vcbot.send_message(vc_player.CHAT_ID, resp, buttons)
    if vc_player.CLEANMODE and event:
        vc_player.EVENTS.append(event)


async def vc_reply(event, text, file=False, edit=False, **kwargs):
    if vc_player.BOTMODE:
        try:
            if file:
                catevent = await catub.tgbot.send_file(
                    event.chat_id, file=file, caption=text, **kwargs
                )
            else:
                catevent = (
                    await catub.tgbot.send_message(event.chat_id, text, **kwargs)
                    if edit
                    else await event.edit(text, **kwargs)
                )
        except Exception:
            await event.reply(
                f"Please disable Bot Mode or Invite {Config.TG_BOT_USERNAME} to the chat"
            )
            edit = False
    elif file:
        catevent = await catub.send_file(event.chat_id, file=file, caption=text)
    elif vc_player.PUBLICMODE:
        catevent = (
            await catub.send_message(event.chat_id, text, **kwargs)
            if edit
            else await event.edit(text, **kwargs)
        )
    else:
        catevent = await edit_or_reply(event, text)
    if vc_player.CLEANMODE and not edit:
        vc_player.EVENTS.append(catevent)
    else:
        return catevent


async def sendmsg(event, res):
    buttons = [
        [
            Button.inline("⏸ Pause", data="pausevc"),
            Button.inline("▶️ Resume", data="resumevc"),
            Button.inline("🔁 repeat", data="repeatvc"),
        ],
        [
            Button.inline("🪡 Skip", data="skipvc"),
            Button.inline("❌ Stop", data="leavevc"),
        ],
        [
            Button.inline("🗑 close", data="vc_close"),
        ],
    ]
    if res and type(res) is list:
        await event.delete()
        event = await vc_reply(event, res[1], file=res[0], buttons=buttons)
    elif res and type(res) is str:
        event = await vc_reply(event, res, buttons)


if __name__ == "__main__":
    asyncio.create_task(vc_player.start())
