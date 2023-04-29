import contextlib
from datetime import datetime

from telethon import functions
from telethon.errors import ChatAdminRequiredError, UserAlreadyInvitedError
from telethon.tl.types import Channel, Chat, User
from telethon.utils import get_display_name
from userbot import catub
from userbot.core.data import _vcusers_list, _sudousers_list
from userbot.core.managers import edit_delete, edit_or_reply
from userbot.helpers.utils import mentionuser
from userbot.sql_helper import global_collectionjson as sql

plugin_category = "extra"


async def get_group_call(chat):
    if isinstance(chat, Channel):
        result = await catub(functions.channels.GetFullChannelRequest(channel=chat))
    elif isinstance(chat, Chat):
        result = await catub(functions.messages.GetFullChatRequest(chat_id=chat.id))
    return result.full_chat.call


async def chat_vc_checker(event, chat, edits=True):
    if isinstance(chat, User):
        await edit_delete(event, "Voice Chats are not available in Private Chats")
        return None
    result = await get_group_call(chat)
    if not result:
        if edits:
            await edit_delete(event, "No Group Call in this chat")
        return None
    return result


async def parse_entity(entity):
    if entity.isnumeric():
        entity = int(entity)
    return await catub.get_entity(entity)


@catub.cat_cmd(
    pattern="vcstart",
    command=("vcstart", plugin_category),
    info={
        "header": "To end a stream on Voice Chat.",
        "description": "To end a stream on Voice Chat",
        "usage": "{tr}vcstart",
        "examples": "{tr}vcstart",
    },
)
async def start_vc(event):
    "To start a Voice Chat."
    vc_chat = await catub.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat, False)
    if gc_call:
        return await edit_delete(event, "Group Call is already available in this chat")
    try:
        await catub(
            functions.phone.CreateGroupCallRequest(
                peer=vc_chat,
                title="Cat VC",
            )
        )
        await edit_delete(event, "Started Group Call")
    except ChatAdminRequiredError:
        await edit_delete(event, "You should be chat admin to start vc", time=20)


@catub.cat_cmd(
    pattern="vcend",
    command=("vcend", plugin_category),
    info={
        "header": "To end a stream on Voice Chat.",
        "description": "To end a stream on Voice Chat",
        "usage": "{tr}vcend",
        "examples": "{tr}vcend",
    },
)
async def end_vc(event):
    "To end a Voice Chat."
    vc_chat = await catub.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    try:
        await catub(functions.phone.DiscardGroupCallRequest(call=gc_call))
        await edit_delete(event, "Group Call Ended")
    except ChatAdminRequiredError:
        await edit_delete(event, "You should be chat admin to kill vc", time=20)


@catub.cat_cmd(
    pattern="vcinv ?(.*)?",
    command=("vcinv", plugin_category),
    info={
        "header": "To invite users on Voice Chat.",
        "usage": "{tr}vcinv < userid/username or reply to user >",
        "examples": [
            "{tr}vcinv @angelpro",
            "{tr}vcinv userid1 userid2",
        ],
    },
)
async def inv_vc(event):
    "To invite users to vc."
    users = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    vc_chat = await catub.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    if not users:
        if not reply:
            return await edit_delete("Whom Should i invite")
        users = reply.from_id
    await edit_or_reply(event, "Inviting User to Group Call")
    entities = str(users).split(" ")
    user_list = []
    for entity in entities:
        cc = await parse_entity(entity)
        if isinstance(cc, User):
            user_list.append(cc)
    try:
        await catub(
            functions.phone.InviteToGroupCallRequest(call=gc_call, users=user_list)
        )
        await edit_delete(event, "Invited users to Group Call")
    except UserAlreadyInvitedError:
        return await edit_delete(event, "User is Already Invited", time=20)


@catub.cat_cmd(
    pattern="vcinfo",
    command=("vcinfo", plugin_category),
    info={
        "header": "To get info of Voice Chat.",
        "usage": "{tr}vcinfo",
        "examples": "{tr}vcinfo",
    },
)
async def info_vc(event):
    "Get info of VC."
    vc_chat = await catub.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    await edit_or_reply(event, "Getting Group Call Info")
    call_details = await catub(
        functions.phone.GetGroupCallRequest(call=gc_call, limit=1)
    )
    grp_call = "**Group Call Info**\n\n"
    grp_call += f"**Title :** {call_details.call.title}\n"
    grp_call += f"**Participants Count :** {call_details.call.participants_count}\n\n"

    if call_details.call.participants_count > 0:
        grp_call += "**Participants**\n"
        for user in call_details.users:
            nam = f"{user.first_name or ''} {user.last_name or ''}"
            grp_call += f"  ● {mentionuser(nam,user.id)} - `{user.id}`\n"
    await edit_or_reply(event, grp_call)


@catub.cat_cmd(
    pattern="vctitle?(.*)?",
    command=("vctitle", plugin_category),
    info={
        "header": "To end a stream on Voice Chat.",
        "description": "To end a stream on Voice Chat",
        "usage": "{tr}vctitle <text>",
        "examples": "{tr}vctitle CatPro",
    },
)
async def title_vc(event):
    "To change vc title."
    title = event.pattern_match.group(1)
    vc_chat = await catub.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    if not title:
        return await edit_delete("What should i keep as title")
    await catub(functions.phone.EditGroupCallTitleRequest(call=gc_call, title=title))
    await edit_delete(event, f"VC title was changed to **{title}**")


@catub.cat_cmd(
    pattern="vc(|un)mute ([\s\S]*)",
    command=("vcmute", plugin_category),
    info={
        "header": "To mute users on Voice Chat.",
        "description": "To mute a stream on Voice Chat",
        "usage": [
            "{tr}vcmute < userid/username or reply to user >",
        ],
        "examples": [
            "{tr}vcmute @angelpro",
            "{tr}vcmute userid1 userid2",
        ],
    },
)
async def mute_vc(event):
    "To mute users in vc."
    cmd = event.pattern_match.group(1)
    users = event.pattern_match.group(2)
    reply = await event.get_reply_message()
    vc_chat = await catub.get_entity(event.chat_id)
    gc_call = await chat_vc_checker(event, vc_chat)
    if not gc_call:
        return
    check = "Unmute" if cmd else "Mute"
    if not users:
        if not reply:
            return await edit_delete(f"Whom Should i {check}")
        users = reply.from_id
    await edit_or_reply(event, f"{check[:-1]}ing User in Group Call")
    entities = str(users).split(" ")
    user_list = []
    for entity in entities:
        cc = await parse_entity(entity)
        if isinstance(cc, User):
            user_list.append(cc)

    for user in user_list:
        await catub(
            functions.phone.EditGroupCallParticipantRequest(
                call=gc_call, participant=user, muted=not cmd
            )
        )
    await edit_delete(event, f"{check}d users in Group Call")


@catub.cat_cmd(
    command=("vcunmute", plugin_category),
    info={
        "header": "To unmute users on Voice Chat.",
        "description": "To unmute a stream on Voice Chat",
        "usage": [
            "{tr}vcunmute < userid/username or reply to user>",
        ],
        "examples": [
            "{tr}vcunmute @angelpro",
            "{tr}vcunmute userid1 userid2",
        ],
    },
)
async def unmute_vc(event):
    "To unmute users in vc."


@catub.cat_cmd(
    pattern="(del|get|add)vcuser(?:\s|$)([\s\S]*)",
    command=("vcuser", plugin_category),
    info={
        "header": "To add user as for vc .",
        "usage": [
            "{tr}addvcuser <username/reply/mention>",
            "{tr}getvcuser",
            "{tr}delvcuser <username/reply/mention>",
        ],
    },
)
async def add_sudo_user(event):
    "To add user to sudo."
    vcusers = {}
    vc_chats = _vcusers_list()
    cmd = event.pattern_match.group(1)

    with contextlib.suppress(AttributeError):
        vcusers = sql.get_collection("vcusers_list").json

    if cmd == "get":
        if not vc_chats:
            return await edit_delete(
                event, "__There are no vc auth users for your Catuserbot.__"
            )
        result = "**The list of vc auth users for your Catuserbot are :**\n\n"
        for chat in [*vcusers]:
            result += f"☞ **Name:** {mentionuser(vcusers[str(chat)]['chat_name'],vcusers[str(chat)]['chat_id'])}\n"
            result += f"**User Id :** `{chat}`\n"
            username = f"@{vcusers[str(chat)]['chat_username']}" or "__None__"
            result += f"**Username :** {username}\n"
            result += f"Added on {vcusers[str(chat)]['date']}\n\n"
        await edit_or_reply(event, result)

    elif cmd in ["add", "del"]:
        replied_user = event.pattern_match.group(2)
        reply = await event.get_reply_message()
        if not replied_user and reply:
            replied_user = reply.from_id
        if replied_user is None:
            return
        replied_user = await catub.get_entity(replied_user)
        if not isinstance(replied_user, User):
            return await edit_delete(event, "`Can't fetch the user...`")

        if cmd == "add":
            if replied_user.id == event.client.uid:
                return await edit_delete(event, "__You already have the access.__.")
            elif replied_user.id in (vc_chats + _sudousers_list()):
                return await edit_delete(
                    event,
                    f"{mentionuser(get_display_name(replied_user),replied_user.id)} __already have access .__",
                )
            date = str(datetime.now().strftime("%B %d, %Y"))
            userdata = {
                "chat_id": replied_user.id,
                "chat_name": get_display_name(replied_user),
                "chat_username": replied_user.username,
                "date": date,
            }

            vcusers[str(replied_user.id)] = userdata
        elif cmd == "del":
            if str(replied_user.id) not in vcusers:
                return await edit_delete(
                    event,
                    f"{mentionuser(get_display_name(replied_user),replied_user.id)} __is not in your vc auth list__.",
                )
            del vcusers[str(replied_user.id)]

        sql.del_collection("vcusers_list")
        sql.add_collection("vcusers_list", vcusers, {})
        output = f"{mentionuser(userdata['chat_name'],userdata['chat_id'])} __is Added to your vc auth users.__\n"
        output += "**Bot is reloading to apply the changes. Please wait for a minute**"
        msg = await edit_or_reply(event, output)
        await event.client.reload(msg)
