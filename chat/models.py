import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

"""
Ensure that token is generated and saved for every new user object created.
"""

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

"""
Represents a user who logs in to the app.
"""

class User(AbstractUser):
    # Primary key uniquely identifying the user.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Username. Making it non unqiue since we don't want to enforce it during sign up.
    # We may enforce uniqueness afterwards when the user creates their profile.
    username = models.CharField(db_index=True, unique=False, max_length=150)

    # Email Address of the user.
    email = models.EmailField(unique=True)

    # Timestamp when this user row was last updated.
    last_updated_time = models.DateTimeField(auto_now=True)

    # One Time Password of the user for activating account/password reset flow.
    otp = models.CharField(max_length=200, default='')

    # Set to True if user's email is verified and False otherwise.
    email_verified = models.BooleanField(default=False)

    USERNAME_FIELD: str = 'email'
    REQUIRED_FIELDS = ['username']


"""
Represents a Chat Room.
"""

class ChatRoom(models.Model):
    # Primary key uniquely identifying the Chat Room.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # User who creates the chat.
    creator_user_id = models.UUIDField(default=uuid.uuid4, editable=False)

    # Timestamp when this Chat Room was created.
    created = models.DateTimeField(auto_now_add=True)

    # Name of the chat room. Can be edited by users.
    name = models.TextField()

    # Timestamp when this Chat was last updated.
    last_updated_time = models.DateTimeField(null=True)

"""
Represents a Chat Message.
"""

class Message(models.Model):
    # Primary key uniquely identifying the Chat Message.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # User who sent the chat message.
    sender_id = models.UUIDField(default=uuid.uuid4, editable=False)

    # Chat Room the message is part of. 
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)

    # Timestamp when this Message was created.
    created_time = models.DateTimeField(auto_now_add=True)

    # Message Text.
    text = models.TextField()    

"""
Represents User level metadata associated with given message.
"""

class UserMessageMetadata(models.Model):
    # Primary key uniquely identifying the User Message.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # User Id (from User table). 
    user_id = models.UUIDField(default=uuid.uuid4, editable=False)

    # Chat Message associated with given User message. 
    message = models.ForeignKey(Message, on_delete=models.CASCADE)

    # Timestamp when message was read.
    read_time = models.DateTimeField(auto_now_add=True)

"""
Represents a Chat Room User.
"""

class ChatRoomUser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Same as primary key in User table.
    user_id = models.UUIDField(default=uuid.uuid4, editable=False)

    # Chat Room the user is part of.
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)

    # Timestamp when this user invited themself to the room.
    invited_time = models.DateTimeField(null=True)

    # Timestamp when the user was accepted to join the room.
    joined_time = models.DateTimeField(null=True)

    # State of the user's membership. Can be INVITED or JOINED.
    state = models.CharField(max_length=200)

     # Timestamp when this row was last updated.
    last_updated_time = models.DateTimeField(auto_now=True)

    # Last time when the chat room was read by the user.
    last_read_time = models.DateTimeField(null=True)

"""
Represents a Post made by a User.
"""

class Post(models.Model):
    # Primary key uniquely identifying the Post.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Creator User. 
    creator_user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Timestamp when this Message was created.
    created_time = models.DateTimeField(auto_now_add=True)

    # Title of post.
    title = models.TextField()

    # Description of post.
    description = models.TextField()

    # Timestamp when this row was last updated.
    last_updated_time = models.DateTimeField(auto_now=True)

"""
Represents feedback provided by a given user about app.
"""

class Feedback(models.Model):
    # Primary key uniquely identifying the Feedback.
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Description of feedback.
    description = models.TextField()

    # User who created the feedback. Has a parent relationsip with feedback. 
    creator_user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Timestamp when this feedback was created.
    created_time = models.DateTimeField(auto_now_add=True)
