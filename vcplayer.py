import contextlib
import logging

from telethon import Button
from telethon.events import InlineQuery
from telethon.tl.types import User
from userbot import Config, catub
from userbot.core.data import _sudousers_list
from userbot.helpers.utils import reply_id

from .helper.function import sendmsg, vc_player, vc_reply
from .helper.stream_helper import Stream
from .helper.tg_downloader import tg_dl

plugin_category = "extra"

logging.getLogger("pytgcalls").setLevel(logging.ERROR)
sudos = [Config.OWNER_ID] + _sudousers_list()


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
    public=True,
)
async def joinVoicechat(event):
    "To join a Voice Chat."
    if not vc_player.PUBLICMODE and event.sender_id not in sudos:
        return
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
        return await vc_reply(event, "Voice Chats are not available in Private Chats")

    if joinas and not vc_chat.username:
        await vc_reply(
            event,
            "Unable to use Join as in Private Chat. Joining as Yourself...",
            edit=True,
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
    public=True,
)
async def leaveVoicechat(event):
    "To leave a Voice Chat."
    if not vc_player.PUBLICMODE and event.sender_id not in sudos:
        return
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
    public=True,
)
async def get_playlist(event):
    "To Get all playlist for Voice Chat."
    if not vc_player.PUBLICMODE and event.sender_id not in sudos:
        return
    event = await vc_reply(event, "Fetching Playlist ......", edit=True)
    if playl := vc_player.PLAYLIST:
        cat = "".join(
            f"{num}. 🔉  `{item['title']}`\n"
            if item["stream"] == Stream.audio
            else f"{num}. �  `{item['title']}`\n"
            for num, item in enumerate(playl, 1)
        )
        await vc_reply(event, f"**Playlist:**\n\n{cat}\n**Enjoy the show**")
    else:
        await vc_reply(event, "Playlist empty")


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
            "{tr}vplay <reply to message/reply to yt link>",
            "{tr}vplay <search song/yt link>",
            "{tr}vplay -f <search song/yt link>",
        ],
        "examples": [
            "{tr}vplay open my letter",
            "{tr}vplay https://www.youtube.com/watch?v=c05GBLT_Ds0",
            "{tr}vplay -f https://www.youtube.com/watch?v=c05GBLT_Ds0",
        ],
    },
    public=True,
)
async def play_video(event):
    "To Play a media as video on VC."
    if event.text.endswith("playlist"):
        return
    if not vc_player.PUBLICMODE and event.sender_id not in sudos:
        return
    chat = event.chat_id
    flag = event.pattern_match.group(1)
    input_str = event.pattern_match.group(2)

    reply = await event.get_reply_message()
    event = await vc_reply(event, "`Searching...`", edit=True)
    if reply and reply.video and not reply.photo:
        inputstr = await tg_dl(event, reply, vc_player.BOTMODE)
    elif reply and reply.message and not input_str:
        inputstr = reply.text
        reply = False
    elif input_str:
        inputstr = input_str
        reply = False
    else:
        return await vc_reply(event, "Please Provide a media file to stream on VC")
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
        resp = await vc_player.play_song(
            event, inputstr, Stream.video, force=True, reply=reply
        )
    else:
        resp = await vc_player.play_song(
            event, inputstr, Stream.video, force=False, reply=reply
        )

    if resp:
        await sendmsg(event, resp)


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
            "{tr}play <reply to message/reply to yt link>",
            "{tr}play <search song/yt link>",
            "{tr}play -f <search song/yt link>",
        ],
        "examples": [
            "{tr}play open my letter",
            "{tr}play https://www.youtube.com/watch?v=c05GBLT_Ds0",
            "{tr}play -f https://www.youtube.com/watch?v=c05GBLT_Ds0",
        ],
    },
    public=True,
)
async def play_audio(event):
    "To Play a media as audio on VC."
    if event.text.endswith("playlist"):
        return
    if not vc_player.PUBLICMODE and event.sender_id not in sudos:
        return
    print("play")
    chat = event.chat_id
    flag = event.pattern_match.group(1)
    input_str = event.pattern_match.group(2)
    reply = await event.get_reply_message()

    event = await vc_reply(event, "`Searching...`", edit=True)
    if reply and reply.media and not reply.photo:
        inputstr = await tg_dl(
            event,
            reply,
        )
    elif reply and reply.message and not input_str:
        inputstr = reply.text
        reply = False
    elif input_str:
        inputstr = input_str
        reply = False
    else:
        return await vc_reply(event, "Please Provide a media file to stream on VC")
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
        resp = await vc_player.play_song(
            event, inputstr, Stream.audio, force=True, reply=reply
        )
    else:
        resp = await vc_player.play_song(
            event, inputstr, Stream.audio, force=False, reply=reply
        )

    if resp:
        await sendmsg(event, resp)


@catub.cat_cmd(
    pattern="previous",
    command=("previous", plugin_category),
    info={
        "header": "To play previous a stream on VC.",
        "description": "To play previou audio or video stream on Voice Chat",
        "usage": [
            "{tr}previous",
        ],
        "examples": [
            "{tr}previous",
        ],
    },
    public=True,
)
async def previous(event):
    "To play previous a stream on Voice Chat."
    if vc_player.PREVIOUS:
        prev = vc_player.PREVIOUS[0]
        song_input = prev["path"]
        stream = prev["stream"]
        duration = prev["duration"]
        url = prev["url"]
        img = prev["img"]
        res = await vc_player.play_song(
            event, song_input, stream, force=True, duration=duration, url=url, img=img
        )
        vc_player.PREVIOUS.pop(0)
        if resp:
            await sendmsg(event, resp)
    else:
        vc_reply(event, "**No previous track found.**")


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
    public=True,
)
async def pause_stream(event):
    "To Pause a stream on Voice Chat."
    if not vc_player.PUBLICMODE and event.sender_id not in sudos:
        return
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
    public=True,
)
async def resume_stream(event):
    "To Resume a stream on Voice Chat."
    if not vc_player.PUBLICMODE and event.sender_id not in sudos:
        return
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
    public=True,
)
async def skip_stream(event):
    if not vc_player.PUBLICMODE and event.sender_id not in sudos:
        return
    "To Skip currently playing stream on Voice Chat."
    event = await vc_reply(event, "Skiping Stream ......", edit=True)
    res = await vc_player.skip()
    if res:
        await sendmsg(event, res)


# =======================INLINE==============================


@catub.cat_cmd(
    pattern="vcplayer$",
    public=True,
)
async def vcplayer(event):
    if not vc_player.PUBLICMODE and event.sender_id not in sudos:
        return
    if vc_player.BOTMODE:
        with contextlib.suppress(Exception):
            return await catub.tgbot.send_message(
                event.chat_id, "** | VC PLAYER | **", buttons=buttons
            )
    reply_to_id = await reply_id(event)
    results = await event.client.inline_query(Config.TG_BOT_USERNAME, "vcplayer")
    await results[0].click(event.chat_id, reply_to=reply_to_id, hide_via=True)
    await event.delete()


@catub.tgbot.on(InlineQuery(pattern="^vcplayer$"))
async def Inlineplayer(event):
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
    await event.answer(
        [
            event.builder.article(
                title=" | VC PLAYER | ", text="** | VC PLAYER | **", buttons=buttons
            )
        ]
    )
