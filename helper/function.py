import asyncio
import logging

from telethon import Button, TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import InviteToChannelRequest, JoinChannelRequest
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


@vc_player.app.on_closed_voice_chat()
async def on_closed_vc(_, update):
    return vc_player.leave_vc()


@vc_player.app.on_stream_end()
async def handler(_, update):
    event = False
    if vc_player.REPEAT:
        return await vc_player.repeat()
    if not vc_player.PLAYLIST:
        if vc_player.CHAT_ID and not vc_player.SILENT:
            return await vc_player.leave_vc()
        else:
            return
    resp = await vc_player.handle_next(update)
    print("In the end it doesnt even matter")
    buttons = [
        [
            Button.inline("⏮ Prev", data="previousvc"),
            Button.inline("⏸ Pause", data="pausevc"),
            Button.inline("⏭ Next", data="skipvc"),
        ],
        [
            Button.inline("🔁 repeat", data="repeatvc"),
            Button.inline("≡ Mainmenu", data="menuvc"),
        ],
        [
            Button.inline("🗑 close", data="vc_close0"),
        ],
    ]
    if vc_player.BOTMODE:
        if resp and type(resp) is list:
            caption = resp[1].split(f"\n\n")[1] if f"\n\n" in resp[1] else resp[1]
            event = await catub.tgbot.send_file(
                vc_player.CHAT_ID, file=resp[0], caption=caption, buttons=buttons
            )
        elif resp and type(resp) is str:
            resp = resp.split(f"\n\n")[1] if f"\n\n" in resp else resp
            event = await catub.tgbot.send_message(
                vc_player.CHAT_ID, resp, buttons=buttons
            )
    else:
        results = await event.client.inline_query(Config.TG_BOT_USERNAME, "vcplayer")
        event = await results[0].click(event.chat_id, hide_via=True)
    if vc_player.CLEANMODE and event:
        vc_player.EVENTS.append(event)


async def check_vcassis(event, vcplayer, vc_chat):
    participants = catub.get_participants(event.chat)
    assis = vcplayer.client.get_me()
    get_id = assis.id
    ids = [int(users.id) for users in participants]
    if get_id not in ids:
        await event.edit("VC assistant will be joining shortly...")
        if username := event.chat.username:
            try:
                await vc_player.client(JoinChannelRequest(username))
                await event.edit(
                    f"VC assistant Joined {event.chat.title} successfully."
                )
            except:
                await event.edit("Failed to join this chat.")
                return False
        else:
            try:
                [await event.client(InviteToChannelRequest(event.chat_id, [get_id]))]

            except Exception:
                await event.edit(
                    "Failed to add VC assistant. Please provide add members right or invite manually."
                )
    return True


async def vc_reply(event, text, file=False, firstmsg=False, dlt=False, **kwargs):
    me = await catub.get_me()
    if vc_player.BOTMODE:
        try:
            if file:
                catevent = await catub.tgbot.send_file(
                    event.chat_id, file=file, caption=text, **kwargs
                )
            else:
                catevent = (
                    await catub.tgbot.send_message(event.chat_id, text, **kwargs)
                    if firstmsg
                    else await event.edit(text, **kwargs)
                )
        except Exception:
            return await event.reply(
                f"Please disable Bot Mode or Invite {Config.TG_BOT_USERNAME} to the chat"
            )
    elif file:
        try:
            results = await event.client.inline_query(
                Config.TG_BOT_USERNAME, "vcplayer"
            )
            catevent = await results[0].click(event.chat_id, hide_via=True)
        except Exception:
            await catub.send_file(event.chat_id, file=file, caption=text, **kwargs)
    elif vc_player.PUBLICMODE:
        catevent = (
            await catub.send_message(event.chat_id, text, **kwargs)
            if firstmsg and event.sender_id != me.id
            else await event.edit(text, **kwargs)
        )
    else:
        catevent = await edit_or_reply(event, text)
    if dlt:
        await asyncio.sleep(dlt)
        return await catevent.delete()
    if vc_player.CLEANMODE and not firstmsg:
        vc_player.EVENTS.append(catevent)
    else:
        return catevent


async def sendmsg(event, res):
    buttons = buttons = [
        [
            Button.inline("⏮ Prev", data="previousvc"),
            Button.inline("⏸ Pause", data="pausevc"),
            # Button.inline("▶️ Resume", data="resumevc"),
            Button.inline("⏭ Next", data="skipvc"),
        ],
        [
            Button.inline("🔁 repeat", data="repeatvc"),
            Button.inline("≡ Mainmenu", data="menuvc"),
        ],
        [
            Button.inline("🗑 close", data="vc_close0"),
        ],
    ]
    if res and type(res) is list:
        await event.delete()
        event = await vc_reply(event, res[1], file=res[0], buttons=buttons)
    elif res and type(res) is tuple:
        event = await vc_reply(event, res[0], dlt=15)
    elif res and type(res) is str:
        event = await vc_reply(event, res, buttons=buttons)


async def inline_edit(event, res, buttons=None):
    if res:
        if type(res) is list:
            try:
                await event.edit(file=res[0], text=res[1], buttons=buttons[1])
            except:
                await event.edit(file=erimg, text=res[1], buttons=buttons[1])
        elif type(res) is str:
            await event.edit(file=vcimg, text=res, buttons=buttons[1])


asyncio.create_task(vc_player.start())
