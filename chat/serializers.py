from rest_framework import serializers
from chat.models import User, Post, Message

"""
Validate that user fields in JSON request.
To separate schema columns from JSON request parameters, we will instantiate
the model instance manually with a helper method instead of using existing Create/Update
helper methods provided by the Serializer class. Same goes for remaining classes as well.
"""

class UserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    user_name = serializers.CharField(max_length=200, allow_blank=False)

    def get_email(self):
        return self.validated_data["email"]

    def get_user_name(self):
        return self.validated_data["user_name"]

    def get_model(self):
        self.is_valid(raise_exception = True)
        return User(email=self.get_email(), username=self.get_user_name())

"""
Validate and Serialize post made by user.
"""

class CreatePostSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    title = serializers.CharField()
    description = serializers.CharField()

    def get_user_id(self):
        return self.validated_data["user_id"]

    def get_title(self):
        return self.validated_data["title"]

    def get_description(self):
        return self.validated_data["description"]

    def get_model(self):
        self.is_valid(raise_exception=True)

        user = User.objects.get(pk=self.get_user_id())
        return Post(creator_user=user, title=self.get_title(), description=self.get_description())

"""
Validate and Serialize Post.
"""

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'creator_user', 'created_time', 'title', 'description']


"""
Validate and serialize ChatRoom.
"""

class CreateChatRoomSerializer(serializers.Serializer):
    creator_id = serializers.UUIDField()
    invitee_id = serializers.UUIDField()
    initial_message = serializers.CharField(allow_blank=False)

    def get_creator_id(self):
        return self.validated_data["creator_id"]

    def get_invitee_id(self):
        return self.validated_data["invitee_id"]

    def get_initial_message(self):
        return self.validated_data["initial_message"]

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['sender_id', 'created_time', 'text']

"""
Manage Chat Accept or Reject.
"""

class ChatAcceptOrRejectSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    room_id = serializers.UUIDField()
    accepted = serializers.BooleanField()

    def get_user_id(self):
        return self.validated_data["user_id"]

    def get_room_id(self):
        return self.validated_data["room_id"]

    def is_accepted(self):
        return self.validated_data["accepted"]
