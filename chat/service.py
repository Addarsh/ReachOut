from chat.serializers import PostSerializer, UserSerializer
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.db import transaction, IntegrityError
from django.db.models.functions import Now
from chat.serializers import UserSerializer, CreatePostSerializer, PostSerializer, CreateChatRoomSerializer
from chat.models import ChatRoomUser, Post, ChatRoom, User, Message

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
                User.objects.get(pk=creator_id)
                User.objects.get(pk=invitee_id)

                # Create ChatRoom
                chat_room  = ChatRoom(creator_user_id=creator_id)
                chat_room.save()

                # Create chat room users.
                room_creator_user = ChatRoomUser(user_id=creator_id, chat_room=chat_room, joined_time= Now())
                room_invitee_user = ChatRoomUser(user_id=invitee_id, chat_room=chat_room, invited_time= Now())
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