import asyncio
from pathlib import Path

import requests
from pytgcalls import PyTgCalls, StreamType
from pytgcalls.exceptions import (
    AlreadyJoinedError,
    NoActiveGroupCall,
    NodeJSNotInstalled,
    NotInGroupCallError,
    TooOldNodeJSVersion,
)
from pytgcalls.types import AudioPiped, AudioVideoPiped
from pytgcalls.types.stream import StreamAudioEnded
from telethon import functions
from telethon.errors import ChatAdminRequiredError
from userbot.helpers.functions import get_ytthumb, yt_search
from userbot.helpers.utils import _catutils
from yt_dlp import YoutubeDL

from .stream_helper import Stream, check_url, video_dl, yt_regex


class CatVC:
    def __init__(self, client) -> None:
        self.app = PyTgCalls(client, overload_quiet_mode=True)
        self.client = client
        self.CHAT_ID = None
        self.CHAT_NAME = None
        self.PLAYING = False
        self.PAUSED = False
        self.MUTED = False
        self.PLAYLIST = []
        self.EVENTS = []
        self.SILENT = True
        self.PUBLICMODE = False
        self.BOTMODE = False
        self.CLEANMODE = False

    async def start(self):
        await self.app.start()

    def clear_vars(self):
        self.CHAT_ID = None
        self.CHAT_NAME = None
        self.PLAYING = False
        self.PAUSED = False
        self.MUTED = False
        self.PLAYLIST = []

    async def join_vc(self, chat, join_as=None):
        self.SILENT = True
        if self.CHAT_ID:
            return f"Already in a group call on {self.CHAT_NAME}"
        if join_as:
            try:
                join_as_chat = await self.client.get_entity(int(join_as))
                join_as_title = f" as **{join_as_chat.title}**"
            except ValueError:
                return "Give Chat Id for joining as"
        else:
            join_as_chat = await self.client.get_me()
            join_as_title = ""
        try:
            await self.app.join_group_call(
                chat_id=chat.id,
                stream=AudioPiped("catvc/resources/Silence01s.mp3"),
                join_as=join_as_chat,
                stream_type=StreamType().pulse_stream,
            )
        except NoActiveGroupCall:
            try:
                await self.client(
                    functions.phone.CreateGroupCallRequest(
                        peer=chat,
                        title="Cat VC",
                    )
                )
                await self.join_vc(chat=chat, join_as=join_as)
            except ChatAdminRequiredError:
                return "You need to become an admin to start VC, or ask one to start"
        except (NodeJSNotInstalled, TooOldNodeJSVersion):
            return "Latest version of NodeJs is not installed"
        except AlreadyJoinedError:
            await self.app.leave_group_call(chat.id)
            await asyncio.sleep(3)
            await self.join_vc(chat=chat, join_as=join_as)
        self.CHAT_ID = chat.id
        self.CHAT_NAME = chat.title
        return f"Joined VC of **{chat.title}**{join_as_title}"

    async def leave_vc(self):
        try:
            await self.app.leave_group_call(self.CHAT_ID)
        except (NotInGroupCallError, NoActiveGroupCall):
            pass
        for event in self.EVENTS:
            try:
                await event.delete()
            except:
                pass
        exts = [
            ".mkv",
            ".mp4",
            ".webm",
            ".m4v",
            ".mp3",
            ".flac",
            ".wav",
            ".m4a",
            ".jpg",
            ".png",
        ]
        for ext in exts:
            await _catutils.runcmd(f"rm -f temp/*{ext}")
        self.CHAT_NAME = None
        self.CHAT_ID = None
        self.PLAYING = False
        self.PLAYLIST = []
        self.EVENTS = []

    async def duration(self, name):
        int_ = int(name)
        ute = int_ // 60
        ond_ = int_ % 60
        if int(ond_) in list(range(0, 10)):
            ond = f"0{ond_}"
        else:
            ond = ond_
        duration = f"{ute}:{ond}"
        return duration

    async def play_song(
        self, event, input, stream=Stream.audio, force=False, reply=False, **kwargs
    ):
        yt_url = False
        img = False
        if not input:
            return
        if reply:
            path = Path(input[0])
            if path.exists():
                if not path.name.endswith(
                    (".mkv", ".mp4", ".webm", ".m4v", ".mp3", ".flac", ".wav", ".m4a")
                ):
                    return "`File is invalid for Streaming`"
                playable = str(path.absolute())
                title = path.name
                duration = await self.duration(reply.file.duration)
                img = input[1]
                url = f"https://t.me/c/{abs(reply.chat_id) if not str(abs(reply.chat_id)).startswith('100') else str(abs(reply.chat_id))[3:]}/{reply.id}"
            else:
                return "`File Path is invalid`"
        elif yt_regex.match(input):
            yt_url = input
        elif check_url(input):
            try:
                res = requests.get(input, allow_redirects=True, stream=True)
                ctype = res.headers.get("Content-Type")
                if "video" not in ctype or "audio" not in ctype:
                    return "INVALID URL"
                name = res.headers.get("Content-Disposition", None)
                if name:
                    title = name.split('="')[0].split('"') or ""
                else:
                    title = input
                playable = input
                url = input
                img = "catvc/resources/404.png"
                duration = "UNKNOWN"
            except Exception as e:
                return f"**INVALID URL**\n\n{e}"
        else:
            path = Path(input)
            if path.exists():
                if not path.name.endswith(
                    (".mkv", ".mp4", ".webm", ".m4v", ".mp3", ".flac", ".wav", ".m4a")
                ):
                    return "`File is invalid for Streaming`"
                playable = str(path.absolute())
                title = path.name
                if kwargs:
                    duration = kwargs["duration"]
                    url = kwargs["url"]
                    img = kwargs["img"]
                else:
                    duration = "UNKNOWN"
                    url = ""
            else:
                yt_url = await yt_search(input)

        if yt_url:
            with YoutubeDL({}) as ytdl:
                ytdl_data = ytdl.extract_info(yt_url, download=False)

                title = ytdl_data.get("title", None)
            if title:
                await event.edit("`Downloading...`")
                playable = await video_dl(yt_url, title)
            else:
                return "Error Fetching URL"

            img = await get_ytthumb(ytdl_data["id"])
            duration = await self.duration(ytdl_data["duration"])
            url = yt_url

        msg = f"**🎧 Playing:** [{title}]({url})\n"
        msg += f"**⏳ Duration:** `{duration}`\n"
        msg += f"**💭 Chat:** `{self.CHAT_NAME}`"
        print(playable)
        if self.PLAYING and not force:
            self.PLAYLIST.append(
                {
                    "title": title,
                    "path": playable,
                    "stream": stream,
                    "img": img,
                    "duration": duration,
                    "url": url,
                }
            )
            return (
                [
                    img,
                    f"**🎧 Added to playlist:** {msg[15:]}\n\n👾 Position: {len(self.PLAYLIST)+1}",
                ]
                if img
                else f"**🎧 Added to playlist:** {msg[15:]}\n\n👾 Position: {len(self.PLAYLIST)+1}"
            )
        if not self.PLAYING:
            self.PLAYLIST.append(
                {
                    "title": title,
                    "path": playable,
                    "stream": stream,
                    "img": img,
                    "duration": duration,
                    "url": url,
                }
            )
            await self.skip()
            return [img, msg] if img else msg
        if force and self.PLAYING:
            self.PLAYLIST.insert(
                0,
                {
                    "title": title,
                    "path": playable,
                    "stream": stream,
                    "img": img,
                    "duration": duration,
                    "url": url,
                },
            )
            await self.skip()
            return [img, msg] if img else msg

    async def handle_next(self, update):
        if isinstance(update, StreamAudioEnded):
            return await self.skip()

    async def skip(self, clear=False):
        self.SILENT = False
        if clear:
            self.PLAYLIST = []
        # log chat name
        if not self.PLAYLIST:
            if self.PLAYING:
                await self.app.change_stream(
                    self.CHAT_ID,
                    AudioPiped("catvc/resources/Silence01s.mp3"),
                )
            self.PLAYING = False
            return "**Skipped Stream\nEmpty Playlist**"

        next = self.PLAYLIST.pop(0)
        if next["stream"] == Stream.audio:
            streamable = AudioPiped(next["path"])
        else:
            streamable = AudioVideoPiped(next["path"])
        try:
            await self.app.change_stream(self.CHAT_ID, streamable)
        except Exception:
            await self.skip()
        self.PLAYING = next
        msg = f"**🌬 Skipped Stream**\n\n"
        msg += f"**🎧 Playing:** [{next['title']}]({next['url']})\n"
        msg += f"**⏳ Duration:** `{next['duration']}`\n"
        msg += f"**💭 Chat:** `{self.CHAT_NAME}`"
        return [next["img"], msg] if next["img"] else msg

    async def pause(self):
        if not self.PLAYING:
            return "Nothing is playing to Pause"
        if not self.PAUSED:
            await self.app.pause_stream(self.CHAT_ID)
            self.PAUSED = True
        return f"Paused Stream on {self.CHAT_NAME}"

    async def resume(self):
        if not self.PLAYING:
            return "Nothing is playing to Resume"
        if self.PAUSED:
            await self.app.resume_stream(self.CHAT_ID)
            self.PAUSED = False
        return f"Resumed Stream on {self.CHAT_NAME}"

    # async def mute(self):
    #     if not self.PLAYING:
    #         return "Nothing is playing to Mute"
    #     if not self.MUTED:
    #         await self.app.mute_stream(self.CHAT_ID)
    #         self.MUTED = True
    #     return f"Muted Stream on {self.CHAT_NAME}"

    # async def unmute(self):
    #     if not self.PLAYING:
    #         return "Nothing is playing to Unmute"
    #     if self.MUTED:
    #         await self.app.unmute_stream(self.CHAT_ID)
    #         self.MUTED = False
    #     return f"Unmuted Stream on {self.CHAT_NAME}"
