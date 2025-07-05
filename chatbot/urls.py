from django.urls import path
from .views import ChatBotAPIView, VoiceAgentAPIView, VoiceTestAPIView

urlpatterns = [
    path('', ChatBotAPIView.as_view(), name='chatbot'),
    path('voice/', VoiceAgentAPIView.as_view(), name='voice_agent'),
    path('voice/test/', VoiceTestAPIView.as_view(), name='voice_agent_test'),
]
