from rest_framework import serializers
from chat.models import User

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
        return User(email=self.get_email(), user_name=self.get_user_name())