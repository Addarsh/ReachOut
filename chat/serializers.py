from rest_framework import serializers
from chat.models import User, Post, Message, Feedback
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

"""
Serialize user information provided during sign up (register). What is key is that password
is encrypted before writing the User object to ensure that future authentication works as expected.
This is because set_password method encrypts the plain text password before saving and the authenticate method (possibly)
in the authentication flow will also encrypt the plain text password. To ensure authentication, we need to do this.
A token is created once the user is saved.
Reference: https://stackoverflow.com/questions/40076254/drf-auth-token-non-field-errors-unable-to-log-in-with-provided-credential
"""

class UserSignUpSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    class Meta:
        model = User
        fields = ['email', 'password']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        user = User(email=validated_data['email'])
        user.set_password(validated_data['password'])
        user.save()
        return user


"""
Login serializer that validates user credentials and authenticates the user.
"""

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:

            user = authenticate(username=email, password=password)

            if user:
                if not user.is_active:
                    raise ValidationError('User account is disabled.')
            else:
                raise ValidationError('Unable to log in with provided credentials.')
        else:
            raise ValidationError('Must include "email" and "password"')

        attrs['user'] = user
        return attrs

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
    title = serializers.CharField()
    description = serializers.CharField()

    def get_title(self):
        return self.validated_data["title"]

    def get_description(self):
        return self.validated_data["description"]

    def get_model(self, user):
        self.is_valid(raise_exception=True)

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
    invitee_id = serializers.UUIDField()
    initial_message = serializers.CharField(allow_blank=False)

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
    room_id = serializers.UUIDField()
    accepted = serializers.BooleanField()

    def get_room_id(self):
        return self.validated_data["room_id"]

    def is_accepted(self):
        return self.validated_data["accepted"]

"""
Manage chat room message post serializer.
"""

class ChatRoomMessagePostSerializer(serializers.Serializer):
    room_id = serializers.UUIDField()
    message = serializers.CharField(max_length=200, allow_blank=False)

    def get_room_id(self):
        return self.validated_data["room_id"]

    def get_message(self):
        return self.validated_data["message"]


class ChatReadSerializer(serializers.Serializer):
    room_id = serializers.UUIDField()

    def get_room_id(self):
        return self.validated_data["room_id"]


class PostIdSerializer(serializers.Serializer):
    id = serializers.UUIDField()

    def get_post_id(self):
        return self.validated_data["id"]


class UsernameSerializer(serializers.Serializer):
    username = serializers.CharField(allow_blank=False)

    def get_user_name(self):
        return self.validated_data["username"]

"""
Validate and Serialize Feedback.
"""

class FeedbackSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=200, allow_blank=False)

    def get_description(self):
        return self.validated_data["description"]
