import re

from telethon.tl.types import User
from telethon import events, Button
from telethon.events import CallbackQuery

from userbot import Config, catub
from userbot.core import check_owner
from userbot.core.managers import edit_delete, edit_or_reply

from .vcplayer import vc_player
from .helper.stream_helper import Stream


plugin_category = "extra"
buttons = [
    [
        [Button.inline("👾 Join VC", data="joinvc")],
        [Button.inline("🍃 Leave VC", data="leavevc")]
    ],
    [
        [Button.inline("▶️ Resume", data="resumevc")],
        [Button.inline("⏸ Pause", data="pausevc")]
    ],
    [
        [Button.inline("🪡 Skip", data="skipvc")],
        [Button.inline("❌ Stop", data="stopvc")]
        ],
        [
            [Button.inline("📜 Playlist", data="playlistvc")],
            [Button.inline("⚙️ Settings", data="settingvc")]
        ]
    ]


@catub.bot_cmd(pattern="^/vchelper$", from_users=Config.OWNER_ID)
async def vchelper(event):
    await event.client.send_message(event.chat_id, ".", buttons=buttons)

@catub.tgbot.on(CallbackQuery(pattern="joinvc"))
@check_owner
async def joinvc(event):
    chat = event.pattern_match.group(1)

    if vc_player.app.active_calls:
        return await event.answer(f"You have already Joined in {vc_player.CHAT_NAME}")

    try:
        vc_chat = await catub.get_entity(chat)
    except Exception as e:
        return await event.answer(f'ERROR : \n{e or "UNKNOWN CHAT"}')

    if isinstance(vc_chat, User):
        return await event.answer("Voice Chats are not available in Private Chats")

    out = await vc_player.join_vc(vc_chat, False)
    await event.answer(out)



@catub.tgbot.on(CallbackQuery(pattern="leavevc"))
@check_owner
async def leavevc(event):
    if vc_player.CHAT_ID:
        chat_name = vc_player.CHAT_NAME
        await vc_player.leave_vc()
        
        await event.answer(f"Left VC of {chat_name}")
    else:
        await event.answer(f"Not yet joined any VC")

    
@catub.tgbot.on(CallbackQuery(pattern="resumevc"))
@check_owner
async def resumevc(event):
    res = await vc_player.resume()
    await event.answer(res)

    
@catub.tgbot.on(CallbackQuery(pattern="pausevc"))
@check_owner
async def pausevc(event):
    res = await vc_player.pause()
    await event.answer(res)

    
@catub.tgbot.on(CallbackQuery(pattern="skipvc"))
@check_owner
async def skipvc(event):
    res = await vc_player.skip()
    if res and type(res) is list:
        await event.delete()
        await event.client.send_file(event.chat_id, file=res[0], caption=res[1])#, time=30)
    elif res and type(res) is str: await event.answer(res)

    
@catub.tgbot.on(CallbackQuery(pattern="repeatvc"))
@check_owner
async def repeatvc(event):
    media = False
    if vc_player.PLAYING:
        input = vc_player.PLAYING['url']
        stream = vc_player.PLAYING['stream']
        if "t.me/c/" in input:
            pass
        else:
            resp = await vc_player.play_song(event, input, stream, force=False, reply=media)
            await event.edit(resp, buttons=buttons)
    else:
        await event.answer("Nothing playing in vc...")

    
@catub.tgbot.on(CallbackQuery(pattern="playlistvc"))
@check_owner
async def playlistvc(event):
    await event.answer(f"Fetching Playlist ......")
    playl = vc_player.PLAYLIST
    if not playl:
        await event.answer(f"Playlist empty")
    else:
        cat = ""
        for num, item in enumerate(playl, 1):
            if item["stream"] == Stream.audio:
                cat += f"{num}. 🔉  `{item['title']}`\n"
            else:
                cat += f"{num}. 📺  `{item['title']}`\n"
        await event.edit(f"**Playlist:**\n\n{cat}\n**Enjoy the show**", buttons=[Button.inline("Back", data="backvc")])

    
@catub.tgbot.on(CallbackQuery(pattern="settingvc"))
@check_owner
async def settingvc(event):
    await event.answer("Wait for update")

    
@catub.tgbot.on(CallbackQuery(pattern="backvc"))
@check_owner
async def vc(event):
    await event.edit(".", buttons=buttons)
