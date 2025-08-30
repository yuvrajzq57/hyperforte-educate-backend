"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from chatbot.views import ChatBotAPIView, ChatHistoryAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/chatbot/', ChatBotAPIView.as_view(), name='chatbot'),
    path('api/chatbot/history/', ChatHistoryAPIView.as_view(), name='chatbot-history'),
    path('api/authent/', include('authent.urls')),
    path('api/', include('profiledetails.urls')),
    path('api/courses/', include('courses.urls')),
    path('api/progress/', include('progress.urls')),
    path('api/studyplan/', include('studyplan.urls')),
    path('', include('attendance.urls')),  # Include attendance URLs
]
