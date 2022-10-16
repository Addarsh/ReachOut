from enum import Enum
from datetime import date, datetime

from chat.models import ChatRoomUser, User, Message

"""
Enum defining current state of user in chat room.
"""

class ChatRoomUserState(Enum):
    INVITED = 1
    JOINED = 2
    REJECTED = 3

"""
Returns dictionary object of chat room.
WARNING: Must be called within transaction context.
"""

def create_chat_room_reponse(user_id, chat_room):

    last_message = Message.objects.order_by('-created_time')[0]
    last_message_dict = {"sender_id": last_message.sender_id, "text": last_message.text, "created_time": last_message.created_time}

    # Query unread messages in room for given user.
    last_read_time = ChatRoomUser.objects.filter(user_id__exact=user_id).get(chat_room__id__exact=chat_room.id).last_read_time
    num_unread_messages = 0
    if last_read_time is None:
        num_unread_messages = len(Message.objects.filter(chat_room__id__exact=chat_room.id))
    else:
        num_unread_messages = len(Message.objects.filter(chat_room__id__exact=chat_room.id).filter(created_time__gt=last_read_time))

    result_room = {"room_id": str(chat_room.id), "name": chat_room.name, "last_updated_time": chat_room.last_updated_time, "last_message":  last_message_dict, "users": [], "num_unread_messages": num_unread_messages}

    chatRoomUsers = ChatRoomUser.objects.filter(chat_room__id__exact=chat_room.id)

    for chatRoomUser in chatRoomUsers:
        # Fetch username info.
        chatUser = User.objects.get(pk=chatRoomUser.user_id)
        result_room["users"].append({"user_id": str(chatUser.id), "state": chatRoomUser.state, 'username': chatUser.username})

    return result_room