from enum import Enum
from datetime import date, datetime

"""
Enum defining current state of user in chat room.
"""

class ChatRoomUserState(Enum):
    INVITED = 1
    JOINED = 2

"""
JSON serializer for objects not serializable by default json code
"""

def json_serial(obj):

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))