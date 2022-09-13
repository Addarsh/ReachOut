import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

"""
Represents a user who logs in to the app.
"""

class User(AbstractUser):
    # Primary key uniquely identifying the user.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Email Address of the user.
    email = models.EmailField(unique=True)

    # User name on the app.
    user_name = models.CharField(max_length=200, blank=False)

    # Timestamp when this user row was last updated.
    last_updated_time = models.DateTimeField(auto_now=True)


"""
Represents a Chat Room.
"""

class ChatRoom(models.Model):
    # Primary key uniquely identifying the Chat Room.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Timestamp when this Chat Room was created.
    created = models.DateTimeField(auto_now_add=True)

    # Timestamp when this Chat was last updated.
    last_updated_time = models.DateTimeField(auto_now=True)

"""
Represents a Chat Message.
"""

class Message(models.Model):
    # Primary key uniquely identifying the Chat Message.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Chat Room Id the message is part of. 
    chat_room_id = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)

    # Timestamp when this Message was created.
    created_time = models.DateTimeField(auto_now_add=True)

    # Message Text.
    text = models.TextField()    


"""
Represents a Chat Room User.
"""

class ChatRoomUser(models.Model):
    # Same as primary key in User table.
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


    # Chat Room Id the user is part of.
    chat_room_id = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)

    # Timestamp when this user invited themself to the room.
    invited_time = models.DateTimeField(auto_now_add=True)

    # Timestamp when the user was accepted to join the room.
    joined_time = models.DateTimeField()

     # Timestamp when this row was last updated.
    last_updated_time = models.DateTimeField(auto_now=True)

"""
Represents a Post made by a User.
"""

class Post(models.Model):
    # Primary key uniquely identifying the Post.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Creator User Id. 
    creator_user_id = models.ForeignKey(User, on_delete=models.CASCADE)

    # Timestamp when this Message was created.
    created_time = models.DateTimeField(auto_now_add=True)

    # Title of post.
    title = models.TextField()

    # Description of post.
    description = models.TextField()

    # Timestamp when this row was last updated.
    last_updated_time = models.DateTimeField(auto_now=True)
