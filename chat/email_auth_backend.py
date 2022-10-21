from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.conf import settings
from django.core.mail import send_mail
from chat.models import User
import random

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password):
                return user
        return None

"""
Send verification email with OTP (one time pin for given user).
Must be called within transaction context.
"""

def verify_email(user: User):
    subject = "Account verification email"
    otp = random.randint(100000, 999999)
    message = "Your one time code is: " + str(otp)
    from_email = settings.DEFAULT_FROM_EMAIL


    # Write OTP to user.
    user.otp = otp
    user.save()

    # Send email.
    send_mail(subject, message, from_email, [user.email])