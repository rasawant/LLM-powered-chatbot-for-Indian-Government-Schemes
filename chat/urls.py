from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('chat/', views.chat_view, name='chat_view'),
    path('clear/', views.clear_chat, name='clear_chat'),
]
