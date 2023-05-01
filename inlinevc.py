import re

from telethon import Button
from telethon.events import CallbackQuery
from telethon.tl.types import User
from userbot import catub
from userbot.core import check_owner

from .helper.function import vc_player
from .helper.stream_helper import Stream

buttons = [
    [
        Button.inline("👾 Join VC", data="joinvc"),
        Button.inline("🍃 Leave VC", data="leavevc"),
    ],
    [
        Button.inline("▶️ Resume", data="resumevc"),
        Button.inline("⏸ Pause", data="pausevc"),
    ],
    [
        Button.inline("🪡 Skip", data="skipvc"),
        Button.inline("🔁 repeat", data="repeatvc"),
    ],
    [
        Button.inline("📜 Playlist", data="playlistvc"),
        Button.inline("⚙️ Settings", data="settingvc"),
    ],
    [
        Button.inline("🗑 close", data="vc_close"),
    ],
]


@catub.tgbot.on(CallbackQuery(data=re.compile(r"^joinvc")))
async def joinvc(event):
    chat = event.chat_id

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


@catub.tgbot.on(CallbackQuery(data=re.compile(r"^leavevc")))
@check_owner
async def leavevc(event):
    if vc_player.CHAT_ID:
        chat_name = vc_player.CHAT_NAME
        await vc_player.leave_vc()

        await event.answer(f"Left VC of {chat_name}")
    else:
        await event.answer("Not yet joined any VC")


@catub.tgbot.on(CallbackQuery(data=re.compile(r"^previousvc")))
@check_owner
async def previousvc(event):
    eve = await event.get_message()
    buttons = [
        [Button.inline(k.text, data=k.data[2:1]) for k in i] for i in eve.buttons
    ]
    if not vc_player.PREVIOUS:
        return await event.answer("No Previous track found.")
    prev = vc_player.PREVIOUS[-1]
    song_input = prev["path"]
    stream = prev["stream"]
    duration = prev["duration"]
    url = prev["url"]
    img = prev["img"]
    res = await vc_player.play_song(
        event,
        song_input,
        stream,
        force=True,
        prev=True,
        duration=duration,
        url=url,
        img=img,
    )
    if res:
        if type(res) is list:
            try:
                await event.edit(res[1], file=res[0], buttons=buttons)
            except Exception:
                await event.edit(res[1], buttons=buttons)
        elif type(res) is str:
            await event.edit(res, buttons=buttons)


@catub.tgbot.on(CallbackQuery(data=re.compile(r"^resumevc(\d)?")))
@check_owner
async def resumevc(event):
    pl = event.pattern_match.group(1)
    res = await vc_player.resume()
    await event.answer(res)
    if pl and not vc_player.PAUSED:
        eve = await event.get_message()
        buttons = [
            [Button.inline(k.text, data=k.data[2:1]) for k in i] for i in eve.buttons
        ]
        buttons[0].pop(1)
        buttons[0].insert(1, Button.inline("⏸ Pause", data="pausevc0"))
        await event.edit(buttons=buttons)


@catub.tgbot.on(CallbackQuery(data=re.compile(r"^pausevc(\d)?")))
@check_owner
async def pausevc(event):
    pl = event.pattern_match.group(1)
    res = await vc_player.pause()
    await event.answer(res)
    if pl and vc_player.PAUSED:
        eve = await event.get_message()
        buttons = [
            [Button.inline(k.text, data=k.data[2:1]) for k in i] for i in eve.buttons
        ]
        buttons[0].pop(1)
        buttons[0].insert(1, Button.inline("▶️ Resume", data="resumevc0"))
        await event.edit(buttons=buttons)


@catub.tgbot.on(CallbackQuery(data=re.compile(r"^skipvc")))
@check_owner
async def skipvc(event):
    eve = await event.get_message()
    buttons = [
        [Button.inline(k.text, data=k.data[2:1]) for k in i] for i in eve.buttons
    ]
    res = await vc_player.skip()
    if res and type(res) is list:
        try:
            await event.edit(res[1], file=res[0], buttons=buttons)
        except Exception:
            await event.edit(res[1], buttons=buttons)
    elif res and type(res) is str:
        await event.edit(res, buttons=buttons)


@catub.tgbot.on(CallbackQuery(data=re.compile(r"^repeatvc")))
async def repeatvc(event):
    eve = await event.get_message()
    buttons = [
        [Button.inline(k.text, data=k.data[2:1]) for k in i] for i in eve.buttons
    ]
    if vc_player.PLAYING:
        song_input = vc_player.PLAYING["path"]
        stream = vc_player.PLAYING["stream"]
        duration = vc_player.PLAYING["duration"]
        url = vc_player.PLAYING["url"]
        img = vc_player.PLAYING["img"]
        res = await vc_player.play_song(
            event, song_input, stream, force=False, duration=duration, url=url, img=img
        )
        if res and type(res) is list:
            await event.edit(res[1], buttons=buttons)
        elif res and type(res) is str:
            await event.edit(res, buttons=buttons)
    else:
        await event.answer("Nothing playing in vc...")


@catub.tgbot.on(CallbackQuery(data=re.compile(r"^playlistvc")))
async def playlistvc(event):
    playl = vc_player.PLAYLIST
    cat = ""
    if not playl and not vc_player.PLAYING:
        return await event.answer("Playlist empty")
    elif vc_player.PLAYING:
        if vc_player.PLAYING["stream"] == Stream.audio:
            cat += f"🎧 Playing. 🔉  `{vc_player.PLAYING['title']}`\n"
        else:
            cat += f"🎧 Playing. 📺  `{vc_player.PLAYING['title']}`\n"
    else:
        await event.answer("Fetching Playlist ......")
    for num, item in enumerate(playl, 1):
        if item["stream"] == Stream.audio:
            cat += f"{num}. 🔉  `{item['title']}`\n"
        else:
            cat += f"{num}. 📺  `{item['title']}`\n"
    await event.edit(
        f"**Playlist:**\n\n{cat}\n**Enjoy the show**",
        buttons=[Button.inline("⬅️ Back", data="backvc")],
    )


@catub.tgbot.on(CallbackQuery(data=re.compile(r"^settingvc")))
@check_owner
async def settingvc(event):
    abtntext = "🏢 Public" if vc_player.PUBLICMODE else "🏠 Private"
    bbtntext = "✅ Enabled" if vc_player.BOTMODE else "❌ Disabled"
    cbtntext = "✅ Enabled" if vc_player.CLEANMODE else "❌ Disabled"
    buttons = [
        [
            Button.inline("🎩 Auth Mode", data="avcinfo"),
            Button.inline(abtntext, data="amode"),
        ],
        [
            Button.inline("🤖 Bot Mode", data="bvcinfo"),
            Button.inline(bbtntext, data="bmode"),
        ],
        [
            Button.inline("🗑 Clean Mode", data="cvcinfo"),
            Button.inline(cbtntext, data="cmode"),
        ],
        [
            Button.inline("⬅️ Back", data="backvc"),
            Button.inline("🗑 close", data="vc_close"),
        ],
    ]
    await event.edit("** | Settings | **", buttons=buttons)


@catub.tgbot.on(CallbackQuery(data=re.compile(r"^backvc")))
@check_owner
async def vc(event):
    await event.edit("** | VC PLAYER | **", buttons=buttons)


@catub.tgbot.on(CallbackQuery(data=re.compile(r"^vc_close(\d)?")))
@check_owner
async def vc(event):
    if del_ := event.pattern_match.group(1):
        return await event.delete()
    await event.edit(
        "**| VC Player Closed |**",
        buttons=[
            [Button.inline("Open again", data="backvc")]
            # [Button.inline("Mode Info", data="modeinfovc")]
        ],
    )


# SETTINGS
@catub.tgbot.on(CallbackQuery(pattern="(a|b|c)mode"))
@check_owner
async def vc(event):
    mode = (event.pattern_match.group(1)).decode("UTF-8")
    cbtntext = "✅ Enabled" if vc_player.CLEANMODE else "❌ Disabled"
    abtntext = "🏢 Public" if vc_player.PUBLICMODE else "🏠 Private"
    bbtntext = "✅ Enabled" if vc_player.BOTMODE else "❌ Disabled"
    if mode == "a":
        if vc_player.PUBLICMODE:
            vc_player.PUBLICMODE = False
            abtntext = "🏠 Private"
        else:
            vc_player.PUBLICMODE = True
            abtntext = "🏢 Public"
    elif mode == "b":
        if vc_player.BOTMODE:
            vc_player.BOTMODE = False
            bbtntext = "❌ Disabled"
        else:
            vc_player.BOTMODE = True
            bbtntext = "✅ Enabled"
    elif mode == "c":
        if vc_player.CLEANMODE:
            vc_player.CLEANMODE = False
            cbtntext = "❌ Disabled"
        else:
            vc_player.CLEANMODE = 30
            cbtntext = "✅ Enabled"

    buttons = [
        [
            Button.inline("🎩 Auth Mode", data="avcinfo"),
            Button.inline(abtntext, data="amode"),
        ],
        [
            Button.inline("🤖 Bot Mode", data="bvcinfo"),
            Button.inline(bbtntext, data="bmode"),
        ],
        [
            Button.inline("🗑 Clean Mode", data="cvcinfo"),
            Button.inline(cbtntext, data="cmode"),
        ],
        [
            Button.inline("⬅️ Back", data="backvc"),
            Button.inline("🗑 close", data="vc_close"),
        ],
    ]

    await event.edit("** | Settings | **", buttons=buttons)


@catub.tgbot.on(CallbackQuery(pattern="(a|b|c)vcinfo"))
@check_owner
async def vc(event):
    mode = (event.pattern_match.group(1)).decode("UTF-8")
    if mode == "a":
        text = "⁉️ What is This?\n\n🏢 Public: Anyone can use catuserbot vc player present in this group.\n\n🏠 Private: Only Owner of user bot and sudo users can use catuserbot vc player"
    elif mode == "b":
        text = "⁉️ What is This?\n\nWhen activated, Your assistant responds to the commands  with interactive buttons"
    elif mode == "c":
        text = "⁉️ What is This?\n\nWhen activated, Bot will delete its message after leaving vc to make your chat clean and clear."
    await event.answer(text)
