import os
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout # authenticate for custom login view
from .serializers import  UserSerializer
# DRF Token Auth
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny # For signup and login views


class SignupAPIView(APIView):
    permission_classes = [AllowAny] # Anyone can access this view

    def post(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "message": "User registered successfully.",
                "token": token.key,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginAPIView(APIView):
    permission_classes = [AllowAny] # Anyone can access this view

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Please provide both username and password'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if user is not None:
            # login(request, user) # Not strictly necessary for token-based auth API, but can be useful if you mix session/token
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Login successful.",
                "token": token.key,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid Credentials'},
                            status=status.HTTP_401_UNAUTHORIZED)

class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated] # Only authenticated users can logout

    def post(self, request, *args, **kwargs):
        try:
            # Delete the token to invalidate it
            request.user.auth_token.delete()
            # logout(request) # If you were using Django sessions
            return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        except (AttributeError, Token.DoesNotExist):
            return Response({"error": "No active session or token found."}, status=status.HTTP_400_BAD_REQUEST)

