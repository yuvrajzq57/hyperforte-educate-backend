#!/usr/bin/env python
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from chatbot.models import GitHubUser
from django.contrib.auth import get_user_model

# Get the custom User model
User = get_user_model()

# Check if you have a GitHub account connected
try:
    # Replace 'your_username' with your actual username
    user = User.objects.first()  # or User.objects.get(username='your_username')
    print(f"Checking for user: {user.username}")
    
    try:
        github_user = GitHubUser.objects.get(user=user)
        print(f"GitHub User found: {github_user}")
        print(f"GitHub Username: {github_user.github_username}")
        print(f"Has access token: {'Yes' if github_user.access_token else 'No'}")
        print(f"Token expires: {github_user.token_expires}")
        print(f"Is token expired: {github_user.is_token_expired()}")
        print(f"Has refresh token: {'Yes' if github_user.refresh_token else 'No'}")
    except GitHubUser.DoesNotExist:
        print("No GitHub account connected for this user")
        
except Exception as e:
    print(f"Error: {e}")
