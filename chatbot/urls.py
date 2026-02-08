from django.urls import path
from chatbot import views

urlpatterns = [
    # Chat message
    path("chat/", views.ChatView.as_view(), name="chat"),

    # Chat lifecycle
    path("new-chat/", views.NewChatView.as_view(), name="new_chat"),
    path("conversations/", views.ConversationListView.as_view(), name="conversations"),
    path("delete-conversation/", views.DeleteConversationView.as_view(), name="delete_conversation"),
]
