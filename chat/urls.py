from django.urls import path

from . import service

urlpatterns = [
    path('user/create/', service.CreateUser.as_view()),
    path('post/', service.PostManager.as_view()),
    path('chats/', service.ChatRoomsPerUserManager.as_view()),
    path('message/', service.MessagesManager.as_view()),
    path('chat-room/', service.ChatRoomManager.as_view()),
    path('chat-room-exists/', service.AlreadyExistingChatRoom.as_view()),
    path('chat-invite/', service.ManageChatInviteRequest.as_view()),
    path('read/', service.MarkChatAsRead.as_view()),
    path('unread-message/', service.UnreadMessagesManager.as_view()),
    path('test/', service.TestAPI.as_view()),
    # Fetch token for given user credentials.
    path('login/', service.Login.as_view()),
    path('signup/', service.SignUp.as_view()),
    path('username/', service.UserNameManager.as_view())
]