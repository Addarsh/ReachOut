from dataclasses import dataclass
from email import message
from http import server
from chat import serializers
from chat.serializers import PostSerializer, UserSerializer
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction, IntegrityError
from django.db.models.functions import Now
from chat.serializers import (
    UserSerializer, 
    CreatePostSerializer, 
    PostSerializer, 
    CreateChatRoomSerializer, 
    MessageSerializer, 
    ChatAcceptOrRejectSerializer, 
    ChatReadSerializer, 
    LoginSerializer, 
    UserSignUpSerializer, 
    PostIdSerializer,
    UsernameSerializer,
    ChatRoomMessagePostSerializer
)
from chat.models import ChatRoomUser, Post, ChatRoom, User, Message, UserMessageMetadata
from chat.common import ChatRoomUserState
from datetime import datetime

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

"""
API to sign up user for the first time.
A token is returned as a result.
"""

class SignUp(APIView):

    def post(self, request):
        serializer = UserSignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
        except Exception as e:
            print(e)
            return Response(data=e.args, status=status.HTTP_400_BAD_REQUEST)

        return Response({'token': token.key, 'user_id': user.pk, 'email': user.email}, status=status.HTTP_201_CREATED)


"""
Custom authentication class for User object. We use this to primarily ensure that
user email and password are used for authentication (Instead of username which is the default).
Once authenticated, we turn the token associated with the user in the response.
"""

class Login(ObtainAuthToken):

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token = Token.objects.get(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
        })

"""
Set username of given user. If username already set, return an error.
"""

class UserNameManager(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UsernameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if user.username != "":
            return Response(data="Username already set", status=status.HTTP_400_BAD_REQUEST)
    
        username = serializer.get_user_name()
        user.username = username
        user.save()
        return Response(data=username, status=status.HTTP_201_CREATED)


"""
API to just test server is working.
"""

class TestAPI(APIView):

    def get(self, request):
        return Response("Hello! Your first response!")

"""
Create a user.
"""

class CreateUser(APIView):

    """
    Create a new user in the database.
    """

    def post(self, request):
        user_serializer = UserSerializer(data=request.data)
        user_serializer.get_model().save()
        return Response(data=user_serializer.data, status=status.HTTP_201_CREATED)

"""
Manage posts on the page.
"""

class PostManager(APIView):

    permission_classes = [IsAuthenticated]

    """
    Create a post.
    """

    def post(self, request):
        created_post_serializer = CreatePostSerializer(data=request.data)
        created_post_serializer.get_model(request.user).save()
        return Response(data=created_post_serializer.data, status=status.HTTP_201_CREATED)

    """
    Returns a list of Posts paginated by created_time.
    """

    def get(self, request):
        # We will return 50 posts at a time.
        limit = 50
        created_time = request.query_params.get('created_time')

        final_posts = []
        try:
            with transaction.atomic():
                posts = []
                if created_time is None:
                    # Return most recent results.
                    posts = Post.objects.order_by('-created_time')[:limit]
                else:
                    posts = Post.objects.filter(created_time__lt=created_time).order_by('-created_time')[:limit]

                # Fetch usernames of each person who created a post.
                usernames = [post.creator_user.username for post in posts]
                serializer = PostSerializer(posts, many=True)
                for i, py_post in enumerate(serializer.data):
                    py_post_copy = py_post.copy()
                    py_post_copy['username'] = usernames[i]
                    final_posts.append(py_post_copy)

        except User.DoesNotExist:
            return Response(data="User not found", status=status.HTTP_400_BAD_REQUEST)
        return Response(data=final_posts, status=status.HTTP_200_OK)

    """
    Delete a post previosuly created by the user.
    """

    def delete(self, request):
        serializer = PostIdSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post_id = serializer.get_post_id()
        try:
            with transaction.atomic():
                post = Post.objects.get(pk=post_id)
                if post.creator_user.id != request.user.id:
                    return Response(data="User not authorized to delete post", status=status.HTTP_401_UNAUTHORIZED)
                post.delete()
        except Post.DoesNotExist:
            return Response(data="Post does not exist", status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


"""
Manage chat room creation.
"""

class ChatRoomManager(APIView):

    permission_classes = [IsAuthenticated]

    """
    Create a chat room and invite user with initial message.
    """

    def post(self, request):
        chat_room_serializer = CreateChatRoomSerializer(data=request.data)
        chat_room_serializer.is_valid(raise_exception = True)
        creator_id = request.user.id

        try:
            with transaction.atomic():
                invitee_id = chat_room_serializer.get_invitee_id()
                initial_message = chat_room_serializer.get_initial_message()

                # Ensure creator and invitee exist in database.
                u1 = User.objects.get(pk=creator_id)
                u2 = User.objects.get(pk=invitee_id)

                # Create ChatRoom
                chat_room_name = ",".join([u1.username, u2.username])
                chat_room  = ChatRoom(creator_user_id=creator_id, name=chat_room_name)
                chat_room.save()

                # Create chat room users.
                room_creator_user = ChatRoomUser(user_id=creator_id, chat_room=chat_room, joined_time= Now(), state=ChatRoomUserState.JOINED.name)
                room_invitee_user = ChatRoomUser(user_id=invitee_id, chat_room=chat_room, invited_time= Now(), state=ChatRoomUserState.INVITED.name)
                room_creator_user.save()
                room_invitee_user.save()

                # Create message.
                initial_message = Message(chat_room=chat_room, text=initial_message, sender_id=creator_id)
                initial_message.save()

                # Mark message as read for sender.
                user_message_metadata = UserMessageMetadata(user_id=creator_id,message=initial_message)
                user_message_metadata.save()

        except User.DoesNotExist:
            print("which user")
            return Response(data="User not found", status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            print(e)
            return Response(data="Internal error", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_201_CREATED)

    """
    List Chats for given user. Should return top 10-20 chats but for now
    returns all.
    """
    
    def get(self, request):
        user_id = request.user.id

        try:
            with transaction.atomic():
                User.objects.get(pk=user_id)

                # Fetch all chat rooms that the user is part of and has not rejected.
                all_chat_rooms = ChatRoom.objects.filter(chatroomuser__user_id__exact=user_id).exclude(chatroomuser__state__exact=ChatRoomUserState.REJECTED.name)
                room_ids = [r.id for r in all_chat_rooms]
                
                # Exclude rooms where the other user is in invited/rejected state. We don't want to show these in the UI.
                chat_room_users = ChatRoomUser.objects.filter(chat_room__id__in=room_ids).exclude(user_id__exact=user_id).exclude(state__in=[ChatRoomUserState.INVITED.name, ChatRoomUserState.REJECTED.name])
                final_room_ids = [r.chat_room.id for r in chat_room_users]
                final_room_ids_set = set(final_room_ids)

                # Query the chat room users.
                final_chat_room_users = ChatRoomUser.objects.filter(chat_room__id__in=final_room_ids)
                final_chat_rooms = list(filter(lambda x: x.id in final_room_ids_set, all_chat_rooms))
                
                results = []
                for chat_room in final_chat_rooms:
                    last_message = Message.objects.order_by('-created_time')[0]
                    last_message_dict = {"sender_id": last_message.sender_id, "text": last_message.text, "created_time": last_message.created_time}

                    # Query unread messages in room for given user.
                    last_read_time = ChatRoomUser.objects.filter(user_id__exact=user_id).get(chat_room__id__exact=chat_room.id).last_read_time
                    num_unread_messages = len(Message.objects.filter(chat_room__id__exact=chat_room.id).filter(created_time__gt=last_read_time))


                    result_room = {"room_id": str(chat_room.id), "name": chat_room.name, "last_message":  last_message_dict, "users": [], "num_unread_messages": num_unread_messages}

                    for chat_user in final_chat_room_users:
                        if chat_user.chat_room.id == chat_room.id:
                            # Fetch username.
                            username = User.objects.get(pk=chat_user.user_id).username
                            result_room["users"].append({"user_id": str(chat_user.user_id), "state": chat_user.state, 'username': username})

                    results.append(result_room)

        except User.DoesNotExist:
            return Response(data="User not found", status=status.HTTP_400_BAD_REQUEST)

        return Response(data=results, status=status.HTTP_200_OK)

"""
Manage chat messages.
"""

class MessagesManager(APIView):

    permission_classes = [IsAuthenticated]

    """
    List Messages in Chat. Should be paginated but for now, return all messages in a chat.
    """

    def get(self, request):
        room_id = request.query_params.get('room_id')
        if room_id is None:
            return Response("Missing Chat Room Id in request", status=status.HTTP_400_BAD_REQUEST)
        user_id = request.user.id
        
        try:
            with transaction.atomic():
                ChatRoom.objects.get(pk=room_id)
                ChatRoomUser.objects.filter(user_id__exact=user_id).get(chat_room__id__exact=room_id)
                messages = Message.objects.filter(chat_room__id__exact=room_id)
                message_serializer = MessageSerializer(messages, many=True)
        except ChatRoom.DoesNotExist:
            return Response(data="Chat Room does not exist", status=status.HTTP_400_BAD_REQUEST)
        except ChatRoomUser.DoesNotExist:
            return Response(data="User does not belong to given chat room", status=status.HTTP_400_BAD_REQUEST)

        return Response(data=message_serializer.data, status=status.HTTP_200_OK)

    """
    Post chat message to given chat room.
    """

    def post(self, request):
        serializer = ChatRoomMessagePostSerializer(data=request.data)
        serializer.is_valid(raise_exception = True)
        user_id = request.user.id
        try:
            with transaction.atomic():
                room_id = serializer.get_room_id()
                message = serializer.get_message()
                chat_room = ChatRoom.objects.get(pk=room_id)
                ChatRoomUser.objects.filter(user_id__exact=user_id).get(chat_room__id__exact=room_id)

                # Create message.
                message = Message(chat_room=chat_room, text=message, sender_id=user_id)
                message.save()
                message_serializer = MessageSerializer(message)

        except ChatRoom.DoesNotExist:
            return Response(data="Chat Room does not exist", status=status.HTTP_400_BAD_REQUEST)
        except ChatRoomUser.DoesNotExist:
            return Response(data="User does not belong to given chat room", status=status.HTTP_400_BAD_REQUEST)

        return Response(data=message_serializer.data, status=status.HTTP_200_OK)
        

"""
Manage Chat Request Invite.
"""

class ManageChatInviteRequest(APIView):

    permission_classes = [IsAuthenticated]

    """
    Accept or reject given chat request invite.
    """

    def post(self, request):
        serializer = ChatAcceptOrRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception = True)

        user_id = request.user.id
        room_id = serializer.get_room_id()
        accepted = serializer.is_accepted()

        try:
            with transaction.atomic():
                User.objects.get(pk=user_id)
                ChatRoom.objects.get(pk=room_id)
                result_state = ChatRoomUserState.JOINED if accepted else ChatRoomUserState.REJECTED

                chat_room_user  = ChatRoomUser.objects.filter(chat_room__id__exact=room_id).get(user_id__exact=user_id)
                if chat_room_user.state != ChatRoomUserState.INVITED.name:
                    return Response(data="User is not currently invited to the room", status=status.HTTP_400_BAD_REQUEST)

                chat_room_user.state = result_state.name
                if result_state == ChatRoomUserState.JOINED:
                    chat_room_user.joined_time = Now()
                
                chat_room_user.save()

                # Mark group as read.
                """
                initial_message = Message.objects.get(chat_room__exact=room_id)
                user_message_metadata = UserMessageMetadata(user_id=user_id, message=initial_message)
                user_message_metadata.save()
                """

        except User.DoesNotExist:
            return Response(data="User does not exist", status=status.HTTP_400_BAD_REQUEST)
        except ChatRoom.DoesNotExist:
            return Response(data="Chat Room does not exist", status=status.HTTP_400_BAD_REQUEST)

        return Response(data="success", status=status.HTTP_200_OK)

"""
Mark Chat Room as read for given user.
"""

class MarkChatAsRead(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatReadSerializer(data=request.data)
        serializer.is_valid(raise_exception = True)
        
        user_id = request.user.id
        room_id = serializer.get_room_id()

        try:
            with transaction.atomic():
                User.objects.get(pk=user_id)
                ChatRoom.objects.get(pk=room_id)

                # Check that user is in joined state and save last read time as now if so.
                chatroom_user = ChatRoomUser.objects.filter(user_id__exact=user_id).filter(chat_room__id__exact=room_id).get(state__exact=ChatRoomUserState.JOINED.name)
                chatroom_user.last_read_time = Now()
                chatroom_user.save()

        except User.DoesNotExist:
            return Response(data="User does not exist", status=status.HTTP_400_BAD_REQUEST)
        except ChatRoom.DoesNotExist:
            return Response(data="Chat Room does not exist", status=status.HTTP_400_BAD_REQUEST)
        except ChatRoomUser.DoesNotExist:
            return Response(data="User is not a member of the room", status=status.HTTP_400_BAD_REQUEST)

        return Response(data="success", status=status.HTTP_200_OK)

"""
Check if there are any unread messgaes for given user.
"""

class AnyUnreadMessagesForUser(APIView):

    permission_classes = [IsAuthenticated]

    """
    Returns a list of unread messages for a user across all chat rooms.
    """

    def get(self, request):
        user_id = request.user.id

        try:
            with transaction.atomic():
                User.objects.get(pk=user_id)

                # Find list of all chat rooms where user is joined.
                chat_room_users = ChatRoomUser.objects.filter(user_id__exact=user_id).filter(state__exact=ChatRoomUserState.JOINED.name)
                room_ids = [r.chat_room.id for r in chat_room_users]

                # In each chat room, find if the latest message is unread by the user or not.
                num_unread_messages = 0
                for id in room_ids:
                    message = Message.objects.filter(chat_room__id__exact=id).order_by('-created_time')[0]

                    # If no results are returned, then the message is unread.
                    user_message_metadata = UserMessageMetadata.objects.filter(message__id__exact=message.id).filter(user_id__exact=user_id)
                    if len(user_message_metadata) == 0:
                        num_unread_messages += 1
                
            
            resp = {'num_unread_messsages': num_unread_messages}
            return Response(data=resp, status=status.HTTP_200_OK)
                    
        except User.DoesNotExist:
            return Response(data="User does not exist", status=status.HTTP_400_BAD_REQUEST)

