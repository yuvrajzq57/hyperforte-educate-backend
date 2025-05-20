from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ProfileDetails
from .serializers import ProfileDetailsSerializer

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def profile_detail(request):
    try:
        profile = ProfileDetails.objects.get(user=request.user)
    except ProfileDetails.DoesNotExist:
        profile = None

    if request.method == 'GET':
        if profile:
            serializer = ProfileDetailsSerializer(profile)
            return Response(serializer.data)
        return Response({'message': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'POST':
        if profile:
            serializer = ProfileDetailsSerializer(profile, data=request.data)
        else:
            serializer = ProfileDetailsSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)