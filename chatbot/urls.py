# # chatbot/urls.py
# from django.urls import path
# from .views import (
#     ChatBotAPIView,
#     VoiceAgentAPIView,
#     VoiceTestAPIView,
#     GitHubOAuthView,
#     GitHubOAuthCallbackView,
#     GitHubStatusView,
#     GitHubDisconnectView,
#     ChatHistoryAPIView  # Add this import
# )

# urlpatterns = [
#     path('', ChatBotAPIView.as_view(), name='chatbot'),
#     path('history/', ChatHistoryAPIView.as_view(), name='chatbot-history'),  # Moved here
#     path('voice/', VoiceAgentAPIView.as_view(), name='voice_agent'),
#     path('voice/test/', VoiceTestAPIView.as_view(), name='voice_agent_test'),
    
#     # GitHub OAuth endpoints
#     path('github/connect/', GitHubOAuthView.as_view(), name='github_connect'),
#     path('github/callback/', GitHubOAuthCallbackView.as_view(), name='github_callback'),
# chatbot/urls.py
from django.urls import path
from .views import (
    GitHubOAuthView,
    GitHubOAuthCallbackView,
    GitHubStatusView,
    GitHubDisconnectView,
    GitHubRepositoriesView
)

urlpatterns = [
    # GitHub OAuth endpoints
    path('github/connect/', GitHubOAuthView.as_view(), name='github_connect'),
    path('github/callback/', GitHubOAuthCallbackView.as_view(), name='github_callback'),
    path('github/status/', GitHubStatusView.as_view(), name='github_status'),
    path('github/repositories/', GitHubRepositoriesView.as_view(), name='github_repositories'),
    path('github/disconnect/', GitHubDisconnectView.as_view(), name='github_disconnect'),
]