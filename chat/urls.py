from django.urls import path

from . import service

urlpatterns = [
    path('user/create/', service.CreateUser.as_view()),
    path('post/', service.PostManager.as_view()),
    path('chat/', service.ChatRoomManager.as_view()),
    path('test/', service.TestAPI.as_view()),
]