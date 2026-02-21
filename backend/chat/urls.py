from django.urls import path

from .views import chat_ollama

urlpatterns = [
    path("", chat_ollama, name="chat_ollama"),
]
