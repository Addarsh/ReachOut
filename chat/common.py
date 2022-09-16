from enum import Enum
from datetime import date, datetime

"""
Enum defining current state of user in chat room.
"""

class ChatRoomUserState(Enum):
    INVITED = 1
    JOINED = 2
    REJECTED = 3