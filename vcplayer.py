import os 
import asyncio
import logging

from telethon.events import CallbackQuery, InlineQuery
from telethon.sessions import StringSession
from telethon import TelegramClient, Button, errors
from telethon.tl.types import User

from userbot.core.managers import edit_or_reply
from userbot.core.data import _sudousers_list
from userbot.helpers.utils import reply_id
from userbot.core import check_owner
from userbot import Config, catub

from .helper.stream_helper import Stream
from .helper.tg_downloader import tg_dl
from .helper.vcp_helper import CatVC

plugin_category = "extra"

logging.getLogger("pytgcalls").setLevel(logging.ERROR)

OWNER_ID = catub.uid
sudos = [OWNER_ID] + _sudousers_list()
vc_session = Config.VC_SESSION

if vc_session:
    vc_client = TelegramClient(
        StringSession(vc_session), Config.APP_ID, Config.API_HASH
    )
else:
    vc_client = catub

vc_client.__class__.__module__ = "telethon.client.telegramclient"
vc_player = CatVC(vc_client)

asyncio.create_task(vc_player.start())


@vc_player.app.on_stream_end()
async def handler(_, update):
    event = False
    resp = await vc_player.handle_next(update)
    vcbot = catub.tgbot if vc_player.BOTMODE else catub
    print("In the end it doesnt even matter")
    if not vc_player.PLAYLIST:
        if vc_player.CHAT_ID and not vc_player.SILENT: return await vc_player.leave_vc()
        else: return
    buttons = [
        [
            Button.inline("⏸ Pause", data="pausevc"),
            Button.inline("▶️ Resume", data="resumevc"),
            Button.inline("🔁 repeat", data="repeatvc")
        ],
        [
            Button.inline("🪡 Skip", data="skipvc"),
            Button.inline("❌ Stop", data="leavevc")
        ],
        [
            Button.inline("🗑 close", data="closepage"),
        ]
    ]
    if resp and type(resp) is list:
        caption = resp[1].split(f'\n\n')[1] if f'\n\n' in resp else resp
        event = await vcbot.send_file(vc_player.CHAT_ID, file=resp[0], caption=caption, buttons=buttons)
    elif resp and type(resp) is str:
        resp = resp.split(f'\n\n')[1] if f'\n\n' in resp else resp
        event = await vcbot.send_message(vc_player.CHAT_ID, resp, buttons)
    if vc_player.CLEANMODE and event:
        vc_player.EVENTS.append(event)

async def vc_reply(event, text, file=False, edit=False, **kwargs):
    if vc_player.BOTMODE:
        if file: 
            catevent = await catub.tgbot.send_file(event.chat_id, file=file, caption=text, **kwargs)
        else:
            if edit: catevent = await catub.tgbot.send_message(event.chat_id, text, **kwargs)
            else: catevent = await event.edit(text, **kwargs)
    else:
        if file:
            catevent = await catub.send_file(event.chat_id, file=file, caption=text)
        else:
            if vc_player.PUBLICMODE:
                if edit: catevent = await catub.send_message(event.chat_id, text, **kwargs)
                else: catevent = await event.edit(text, **kwargs)
            else: catevent = await edit_or_reply(event, text)
    if vc_player.CLEANMODE and not edit:
        vc_player.EVENTS.append(catevent)
    else:
        return catevent


async def sendmsg(event, res):
    buttons = [
        [
            Button.inline("⏸ Pause", data="pausevc"),
            Button.inline("▶️ Resume", data="resumevc"),
            Button.inline("🔁 repeat", data="repeatvc")
        ],
        [
            Button.inline("🪡 Skip", data="skipvc"),
            Button.inline("❌ Stop", data="leavevc")
        ],
        [
            Button.inline("🗑 close", data="closepage"),
        ]
    ]
    if res and type(res) is list:
        await event.delete()
        event = await vc_reply(event,  res[1], file=res[0], buttons=buttons)
    elif res and type(res) is str: event = await vc_reply(event, res, buttons)
    


ALLOWED_USERS = set()


@catub.cat_cmd(
    pattern="joinvc ?(\S+)? ?(?:-as)? ?(\S+)?",
    command=("joinvc", plugin_category),
    info={
        "header": "To join a Voice Chat.",
        "description": "To join or create and join a Voice Chat",
        "note": "You can use -as flag to join anonymously",
        "flags": {
            "-as": "To join as another chat.",
        },
        "usage": [
            "{tr}joinvc",
            "{tr}joinvc (chat_id)",
            "{tr}joinvc -as (peer_id)",
            "{tr}joinvc (chat_id) -as (peer_id)",
        ],
        "examples": [
            "{tr}joinvc",
            "{tr}joinvc -1005895485",
            "{tr}joinvc -as -1005895485",
            "{tr}joinvc -1005895485 -as -1005895485",
        ],
    },
    public=True
)
async def joinVoicechat(event):
    "To join a Voice Chat."
    if not vc_player.PUBLICMODE and event.sender_id not in sudos: return
    chat = event.pattern_match.group(1)
    joinas = event.pattern_match.group(2)

    event = await vc_reply(event, "Joining VC ......", edit=True)

    if chat and chat != "-as":
        if chat.strip("-").isnumeric():
            chat = int(chat)
    else:
        chat = event.chat_id

    if vc_player.app.active_calls:
        return await vc_reply(
            event, f"You have already Joined in {vc_player.CHAT_NAME}"
        )

    try:
        vc_chat = await catub.get_entity(chat)
    except Exception as e:
        return await vc_reply(event, f'ERROR : \n{e or "UNKNOWN CHAT"}')

    if isinstance(vc_chat, User):
        return await vc_reply(
            event, "Voice Chats are not available in Private Chats"
        )

    if joinas and not vc_chat.username:
        await vc_reply(
            event, "Unable to use Join as in Private Chat. Joining as Yourself...", edit=True
        )
        joinas = False

    out = await vc_player.join_vc(vc_chat, joinas)
    await vc_reply(event, out)


@catub.cat_cmd(
    pattern="leavevc",
    command=("leavevc", plugin_category),
    info={
        "header": "To leave a Voice Chat.",
        "description": "To leave a Voice Chat",
        "usage": [
            "{tr}leavevc",
        ],
        "examples": [
            "{tr}leavevc",
        ],
    },
    public=True
)
async def leaveVoicechat(event):
    "To leave a Voice Chat."
    if not vc_player.PUBLICMODE and event.sender_id not in sudos: return
    if vc_player.CHAT_ID:
        event = await vc_reply(event, "Leaving VC ......", edit=True)
        chat_name = vc_player.CHAT_NAME
        await vc_player.leave_vc()
        
        await vc_reply(event, f"Left VC of {chat_name}")
    else:
        await vc_reply(event, "Not yet joined any VC")


@catub.cat_cmd(
    pattern="playlist$",
    command=("playlist", plugin_category),
    info={
        "header": "To Get all playlist.",
        "description": "To Get all playlist for Voice Chat.",
        "usage": [
            "{tr}playlist",
        ],
        "examples": [
            "{tr}playlist",
        ],
    },
    public=True
)
async def get_playlist(event):
    "To Get all playlist for Voice Chat."
    if not vc_player.PUBLICMODE and event.sender_id not in sudos: return
    event = await vc_reply(event, "Fetching Playlist ......", edit=True)
    playl = vc_player.PLAYLIST
    if not playl:
        await vc_reply(event, "Playlist empty")
    else:
        cat = ""
        for num, item in enumerate(playl, 1):
            if item["stream"] == Stream.audio:
                cat += f"{num}. 🔉  `{item['title']}`\n"
            else:
                cat += f"{num}. 📺  `{item['title']}`\n"
        await vc_reply(event, f"**Playlist:**\n\n{cat}\n**Enjoy the show**")


@catub.cat_cmd(
    pattern="vplay ?(-f)? ?([\S ]*)?",
    command=("vplay", plugin_category),
    info={
        "header": "To Play a media as video on VC.",
        "description": "To play a video stream on VC.",
        "flags": {
            "-f": "Force play the Video",
        },
        "usage": [
            "{tr}vplay (reply to message)",
            "{tr}vplay (yt link)",
            "{tr}vplay -f (yt link)",
        ],
        "examples": [
            "{tr}vplay",
            "{tr}vplay https://www.youtube.com/watch?v=c05GBLT_Ds0",
            "{tr}vplay -f https://www.youtube.com/watch?v=c05GBLT_Ds0",
        ],
    },
    public=True
)
async def play_video(event):
    "To Play a media as video on VC."
    if event.text.endswith("playlist"): return
    if not vc_player.PUBLICMODE and event.sender_id not in sudos: return
    chat = event.chat_id
    flag = event.pattern_match.group(1)
    input_str = event.pattern_match.group(2)

    reply = await event.get_reply_message()
    event = await vc_reply(event, "`Searching...`", edit=True)
    if reply and reply.video and not reply.photo:
        inputstr = await tg_dl(event)
    elif reply and reply.message and not input_str:
        inputstr = reply.text
        reply = False
    elif input_str:
        inputstr = input_str
        reply = False
    else:
        return await vc_reply(
            event, "Please Provide a media file to stream on VC"
        )
    if not vc_player.CHAT_ID:
        try:
            vc_chat = await catub.get_entity(chat)
        except Exception as e:
            return await vc_reply(event, f'ERROR : \n{e or "UNKNOWN CHAT"}')
        if isinstance(vc_chat, User):
            return await vc_reply(
                event, "Voice Chats are not available in Private Chats"
            )
        out = await vc_player.join_vc(vc_chat, False)
    
    if flag:
        resp = await vc_player.play_song(event, inputstr, Stream.video, force=True, reply=reply)
    else:
        resp = await vc_player.play_song(event, inputstr, Stream.video, force=False, reply=reply)

    if resp: await sendmsg(event, resp)
    

    # if input_str == "" and event.reply_to_msg_id:
    #     input_str = await tg_dl(event)
    # if not input_str:
    #     return await edit_delete(
    #         event, "Please Provide a media file to stream on VC", time=20
    #     )
    # if not vc_player.CHAT_ID:
    #     return await edit_or_reply(event, "Join a VC and use play command")
    # if not input_str:
    #     return await edit_or_reply(event, "No Input to play in vc")
    # await edit_or_reply(event, "Playing in VC ......")
    # if flag:
    #     resp = await vc_player.play_song(input_str, Stream.video, force=True)
    # else:
    #     resp = await vc_player.play_song(input_str, Stream.video, force=False)
    # if resp:
    #     await edit_delete(event, resp, time=30)


@catub.cat_cmd(
    pattern="play ?(-f)? ?([\S ]*)?$",
    command=("play", plugin_category),
    info={
        "header": "To Play a media as audio on VC.",
        "description": "To play a audio stream on VC.",
        "flags": {
            "-f": "Force play the Audio",
        },
        "usage": [
            "{tr}play (reply to message)",
            "{tr}play (yt link)",
            "{tr}play -f (yt link)",
        ],
        "examples": [
            "{tr}play",
            "{tr}play https://www.youtube.com/watch?v=c05GBLT_Ds0",
            "{tr}play -f https://www.youtube.com/watch?v=c05GBLT_Ds0",
        ],
    },
    public=True
)
async def play_audio(event):
    "To Play a media as audio on VC."
    if event.text.endswith("playlist"): return
    if not vc_player.PUBLICMODE and event.sender_id not in sudos: return
    print("play")
    chat = event.chat_id
    flag = event.pattern_match.group(1)
    input_str = event.pattern_match.group(2)
    reply = await event.get_reply_message()
    
    event = await vc_reply(event, "`Searching...`", edit=True)
    if reply and reply.media and not reply.photo:
        inputstr = await tg_dl(event, reply)
    elif reply and reply.message and not input_str:
        inputstr = reply.text
        reply = False
    elif input_str:
        inputstr = input_str
        reply = False
    else:
        return await vc_reply(
            event, "Please Provide a media file to stream on VC"
        )
    if not vc_player.CHAT_ID:
        try:
            vc_chat = await catub.get_entity(chat)
        except Exception as e:
            return await vc_reply(event, f'ERROR : \n{e or "UNKNOWN CHAT"}')
        if isinstance(vc_chat, User):
            return await vc_reply(
                event, "Voice Chats are not available in Private Chats"
            )
        await vc_player.join_vc(vc_chat, False)
    
    if flag:
        resp = await vc_player.play_song(event, inputstr, Stream.audio, force=True, reply=reply)
    else:
        resp = await vc_player.play_song(event, inputstr, Stream.audio, force=False, reply=reply)

    if resp: await sendmsg(event, resp)

    # if input_str == "" and event.reply_to_msg_id:
    #     input_str = await tg_dl(event)
    # if not input_str:
    #     return await edit_delete(
    #         event, "Please Provide a media file to stream on VC", time=20
    #     )
    # if not vc_player.CHAT_ID:
    #     return await edit_or_reply(event, "Join a VC and use play command")
    # if not input_str:
    #     return await edit_or_reply(event, "No Input to play in vc")
    # await edit_or_reply(event, "Playing in VC ......")
    # if flag:
    #     resp = await vc_player.play_song(input_str, Stream.audio, force=True)
    # else:
    #     resp = await vc_player.play_song(input_str, Stream.audio, force=False)
    # if resp:
    #     await edit_delete(event, resp, time=30)


@catub.cat_cmd(
    pattern="pause",
    command=("pause", plugin_category),
    info={
        "header": "To Pause a stream on Voice Chat.",
        "description": "To Pause a stream on Voice Chat",
        "usage": [
            "{tr}pause",
        ],
        "examples": [
            "{tr}pause",
        ],
    },
    public=True
)
async def pause_stream(event):
    "To Pause a stream on Voice Chat."
    if not vc_player.PUBLICMODE and event.sender_id not in sudos: return
    event = await vc_reply(event, "Pausing VC ......", edit=True)
    res = await vc_player.pause()
    await vc_reply(event, res)


@catub.cat_cmd(
    pattern="resume",
    command=("resume", plugin_category),
    info={
        "header": "To Resume a stream on Voice Chat.",
        "description": "To Resume a stream on Voice Chat",
        "usage": [
            "{tr}resume",
        ],
        "examples": [
            "{tr}resume",
        ],
    },
    public=True
)
async def resume_stream(event):
    "To Resume a stream on Voice Chat."
    if not vc_player.PUBLICMODE and event.sender_id not in sudos: return
    event = await vc_reply(event, "Resuming VC ......", edit=True)
    res = await vc_player.resume()
    await vc_reply(event, res)


@catub.cat_cmd(
    pattern="skip",
    command=("skip", plugin_category),
    info={
        "header": "To Skip currently playing stream on Voice Chat.",
        "description": "To Skip currently playing stream on Voice Chat.",
        "usage": [
            "{tr}skip",
        ],
        "examples": [
            "{tr}skip",
        ],
    },
    public=True
)
async def skip_stream(event):
    if not vc_player.PUBLICMODE and event.sender_id not in sudos: return
    "To Skip currently playing stream on Voice Chat."
    event = await vc_reply(event, "Skiping Stream ......", edit=True)
    res = await vc_player.skip()
    if res: await sendmsg(event, res)


"""
@catub.cat_cmd(
    pattern="a(?:llow)?vc ?([\d ]*)?",
    command=("allowvc", plugin_category),
    info={
        "header": "To allow a user to control VC.",
        "description": "To allow a user to controll VC.",
        "usage": [
            "{tr}allowvc",
            "{tr}allowvc (user id)",
        ],
    },
)
async def allowvc(event):
    "To allow a user to controll VC."
    user_id = event.pattern_match.group(1)
    if user_id:
        user_id = user_id.split(" ")
    if not user_id and event.reply_to_msg_id:
        reply = await event.get_reply_message()
        user_id = [reply.from_id]
    if not user_id:
        return await edit_delete(event, "Whom should i Add")
    ALLOWED_USERS.update(user_id)
    return await edit_delete(event, "Added User to Allowed List")


@catub.cat_cmd(
    pattern="d(?:isallow)?vc ?([\d ]*)?",
    command=("disallowvc", plugin_category),
    info={
        "header": "To disallowvc a user to control VC.",
        "description": "To disallowvc a user to controll VC.",
        "usage": [
            "{tr}disallowvc",
            "{tr}disallowvc (user id)",
        ],
    },
)
async def disallowvc(event):
    "To allow a user to controll VC."
    user_id = event.pattern_match.group(1)
    if user_id:
        user_id = user_id.split(" ")
    if not user_id and event.reply_to_msg_id:
        reply = await event.get_reply_message()
        user_id = [reply.from_id]
    if not user_id:
        return await edit_delete(event, "Whom should i remove")
    ALLOWED_USERS.difference_update(user_id)
    return await edit_delete(event, "Removed User to Allowed List")


@catub.on(
    events.NewMessage(outgoing=True, pattern=f"{tr}(speak|sp)(h|j)?(?:\s|$)([\s\S]*)")
)  #only for catub client
async def speak(event):
    "Speak in vc"
    r = event.pattern_match.group(2)
    input_str = event.pattern_match.group(3)
    re = await event.get_reply_message()
    if ";" in input_str:
        lan, text = input_str.split(";")
    else:
        if input_str:
            text = input_str
        elif re and re.text and not input_str:
            text = re.message
        else:
            return await event.delete()
        if r == "h":
            lan = "hi"
        elif r == "j":
            lan = "ja"
        else:
            lan = "en"
    text = deEmojify(text.strip())
    lan = lan.strip()
    if not os.path.isdir("./temp/"):
        os.makedirs("./temp/")
    file = "./temp/" + "voice.ogg"
    try:
        tts = gTTS(text, lang=lan)
        tts.save(file)
        cmd = [
            "ffmpeg",
            "-i",
            file,
            "-map",
            "0:a",
            "-codec:a",
            "libopus",
            "-b:a",
            "100k",
            "-vbr",
            "on",
            file + ".opus",
        ]
        try:
            t_response = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except (subprocess.CalledProcessError, NameError, FileNotFoundError) as exc:
            await edit_or_reply(event, str(exc))
        else:
            os.remove(file)
            file = file + ".opus"
        await vc_player.play_song(file, Stream.audio, force=False)
        await event.delete()
        os.remove(file)
    except Exception as e:
         await edit_or_reply(event, f"**Error:**\n`{e}`")
"""

#INLINE

buttons = [
    [
        Button.inline("👾 Join VC", data="joinvc"),
        Button.inline("🍃 Leave VC", data="leavevc")
    ],
    [
        Button.inline("▶️ Resume", data="resumevc"),
        Button.inline("⏸ Pause", data="pausevc")
    ],
    [
        Button.inline("🪡 Skip", data="skipvc"),
        Button.inline("🔁 repeat", data="repeatvc")
    ],
    [
        Button.inline("📜 Playlist", data="playlistvc"),
        Button.inline("⚙️ Settings", data="settingvc")
    ],
    [
        Button.inline("🗑 close", data="closepage"),
    ]
]

@catub.tgbot.on(InlineQuery(pattern="^vcplayer$"))
async def Inlineplayer(event):
    await event.answer([event.builder.article(title=" | VC PLAYER | ", text="** | VC PLAYER | **", buttons=buttons)])


@catub.cat_cmd(pattern="vcplayer$")
async def vcplayer(event):
    if vc_player.BOTMODE:
        try:
            return await catub.tgbot.send_message(event.chat_id, "** | VC PLAYER | **", buttons=buttons)
        except:
            pass
    reply_to_id = await reply_id(event)
    results = await event.client.inline_query(Config.TG_BOT_USERNAME, "vcplayer")
    await results[0].click(event.chat_id, reply_to=reply_to_id, hide_via=True)
    await event.delete()

@catub.tgbot.on(CallbackQuery(pattern="joinvc"))
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
    if res and type(res) is list: await event.edit(res[1], buttons=buttons)
    elif res and type(res) is str: await event.answer(res)

    
@catub.tgbot.on(CallbackQuery(pattern="repeatvc"))
async def repeatvc(event):
    if vc_player.PLAYING:
        input = vc_player.PLAYING['path']
        stream = vc_player.PLAYING['stream']
        duration = vc_player.PLAYING['duration']
        url = vc_player.PLAYING['url']
        img = vc_player.PLAYING['img']
        res = await vc_player.play_song(event, input, stream, force=False, duration=duration, url=url, img=img)
        if res and type(res) is list: await event.edit(res[1], buttons=buttons)
        elif res and type(res) is str: await event.answer(res)
    else:
        await event.answer("Nothing playing in vc...")

    
@catub.tgbot.on(CallbackQuery(pattern="playlistvc"))
async def playlistvc(event):
    playl = vc_player.PLAYLIST
    if not playl:
        await event.answer(f"Playlist empty")
    else:
        await event.answer(f"Fetching Playlist ......")
        cat = ""
        for num, item in enumerate(playl, 1):
            if item["stream"] == Stream.audio:
                cat += f"{num}. 🔉  `{item['title']}`\n"
            else:
                cat += f"{num}. 📺  `{item['title']}`\n"
        await event.edit(f"**Playlist:**\n\n{cat}\n**Enjoy the show**", buttons=[Button.inline("⬅️ Back", data="backvc")])

    
@catub.tgbot.on(CallbackQuery(pattern="settingvc"))
@check_owner
async def settingvc(event):
    abtntext = "🏠 Private"
    bbtntext = "❌ Disabled"
    cbtntext = "❌ Disabled"
    if vc_player.PUBLICMODE: abtntext = "🏢 Public"
    if vc_player.BOTMODE: bbtntext = "✅ Enabled"
    if vc_player.CLEANMODE: cbtntext = "✅ Enabled"
    buttons = [
        [Button.inline("🎩 Auth Mode", data="amodeinfo"), Button.inline(abtntext, data="amode")],
        [Button.inline("🤖 Bot Mode", data="bmodeinfo"), Button.inline(bbtntext, data="bmode")],
        [Button.inline("🗑 Clean Mode", data="cmodeinfo"), Button.inline(cbtntext, data="cmode")],
        [Button.inline("⬅️ Back", data="backvc"), Button.inline("🗑 close", data="closepage")],
    ]
    await event.edit("** | Settings | **", buttons=buttons)

    
@catub.tgbot.on(CallbackQuery(pattern="backvc"))
@check_owner
async def vc(event):
    await event.edit("** | VC PLAYER | **", buttons=buttons)


@catub.tgbot.on(CallbackQuery(pattern="closepage"))
@check_owner
async def vc(event):
    await event.delete()




#SETTINGS
@catub.tgbot.on(CallbackQuery(pattern="(a|b|c)mode"))
@check_owner
async def vc(event):
    mode = (event.pattern_match.group(1)).decode("UTF-8")
    abtntext = "🏠 Private"
    bbtntext = "❌ Disabled"
    cbtntext = "❌ Disabled"
    if vc_player.PUBLICMODE: abtntext = "🏢 Public"
    if vc_player.BOTMODE: bbtntext = "✅ Enabled"
    if vc_player.CLEANMODE: cbtntext = "✅ Enabled"
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
        [Button.inline("🎩 Auth Mode", data="amodeinfo"), Button.inline(abtntext, data="amode")],
        [Button.inline("🤖 Bot Mode", data="bmodeinfo"), Button.inline(bbtntext, data="bmode")],
        [Button.inline("🗑 Clean Mode", data="cmodeinfo"), Button.inline(cbtntext, data="cmode")],
        [Button.inline("⬅️ Back", data="backvc"), Button.inline("🗑 close", data="closepage")],
    ]

    await event.edit("** | Settings | **", buttons=buttons)


@catub.tgbot.on(CallbackQuery(pattern="(a|b|c)modeinfo"))
@check_owner
async def vc(event):
    mode = (event.pattern_match.group(1)).decode("UTF-8")
    if mode == "a": text = "AUTH mode"
    if mode == "b": text = "Choose whether to use bot or user client"
    if mode == "c": text = "Clean Mode - When enabled messages get deleted after 30 secs automatically"
    await event.answer(text)
