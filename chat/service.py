from chat.serializers import PostSerializer, UserSerializer
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.db import transaction, IntegrityError
from django.db.models.functions import Now
from chat.serializers import UserSerializer, CreatePostSerializer, PostSerializer, CreateChatRoomSerializer
from chat.models import ChatRoomUser, Post, ChatRoom, User, Message
from chat.common import ChatRoomUserState, json_serial
import json

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

    """
    Create a post.
    """

    def post(self, request):
        created_post_serializer = CreatePostSerializer(data=request.data)
        created_post_serializer.get_model().save()
        return Response(data=created_post_serializer.data, status=status.HTTP_201_CREATED)

    """
    Returns a list of Posts. Ideally we want this to be a paginated list but for now, we will
    just return all the posts available in the database in decreasing order of creation time.
    """

    def get(self, request):
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

"""
Manage chat room creation.
"""

class ChatRoomManager(APIView):

    """
    Create a chat room and invite user with initial message.
    """

    def post(self, request):
        chat_room_serializer = CreateChatRoomSerializer(data=request.data)
        chat_room_serializer.is_valid(raise_exception = True)

        try:
            with transaction.atomic():
                creator_id = chat_room_serializer.get_creator_id()
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

        except User.DoesNotExist:
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
        user_id = request.query_params.get('user_id')
        if user_id is None:
            return Response("Missing User in request", status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                User.objects.get(pk=user_id)

                # Fetch all chat rooms that the user is part of.
                all_chat_rooms = ChatRoom.objects.filter(chatroomuser__user_id__exact=user_id)
                room_ids = [r.id for r in all_chat_rooms]
                
                # Exclude rooms where the other user is in invited state. We don't want to show these in the UI.
                chat_room_users = ChatRoomUser.objects.filter(chat_room__id__in=room_ids).exclude(user_id__exact=user_id).exclude(state__exact=ChatRoomUserState.INVITED.name)
                final_room_ids = [r.chat_room.id for r in chat_room_users]
                final_room_ids_set = set(final_room_ids)

                # Query the chat room users.
                final_chat_room_users = ChatRoomUser.objects.filter(chat_room__id__in=final_room_ids)
                final_chat_rooms = list(filter(lambda x: x.id in final_room_ids_set, all_chat_rooms))
                
                results = []
                for chat_room in final_chat_rooms:
                    last_message = Message.objects.order_by('-created_time')[0]
                    last_message_dict = {"sender_id": str(last_message.sender_id), "text": last_message.text, "created_time": last_message.created_time}
                    result_room = {"room_id": str(chat_room.id), "name": chat_room.name, "last_message":  last_message_dict,"users": []}

                    for chat_user in final_chat_room_users:
                        if chat_user.chat_room.id == chat_room.id:
                            result_room["users"].append({"user_id": str(chat_user.user_id), "state": chat_user.state})

                    results.append(result_room)

                json_result = json.dumps(results, default=json_serial)

        except User.DoesNotExist:
            return Response(data="User not found", status=status.HTTP_400_BAD_REQUEST)


        return Response(data=json_result, status=status.HTTP_200_OK)