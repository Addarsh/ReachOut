from django.urls import path

from . import service

urlpatterns = [
    path('', service.ChatList.as_view()),
]