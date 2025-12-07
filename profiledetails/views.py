from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ProfileDetails
from .serializers import ProfileDetailsSerializer

import logging

logger = logging.getLogger(__name__)

@api_view(['GET', 'POST', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile_detail(request):
    """
    Handle profile details with support for GET, POST, PUT, and PATCH methods.
    Automatically creates a profile if it doesn't exist for GET requests.
    """
    try:
        logger.info(f"Processing {request.method} request for user {request.user.id}")

        if request.method == 'GET':
            try:
                profile = ProfileDetails.objects.get(user=request.user)
                logger.info(f"Found existing profile for user {request.user.id}")
            except ProfileDetails.DoesNotExist:
                # Create a new profile with default values
                logger.info(f"Creating new profile for user {request.user.id}")
                profile = ProfileDetails.objects.create(
                    user=request.user,
                    about='',
                    background='',
                    student_type='',
                    preferred_learning_style='',
                    learning_preference='',
                    strengths=[],
                    weaknesses=[]
                )
            
            serializer = ProfileDetailsSerializer(profile)
            return Response(serializer.data)

        # Handle POST, PUT, PATCH
        data = request.data.copy()
        
        # Map description to about for frontend compatibility
        if 'description' in data and 'about' not in data:
            data['about'] = data['description']
        
        try:
            profile = ProfileDetails.objects.get(user=request.user)
            serializer = ProfileDetailsSerializer(profile, data=data, partial=request.method in ['PATCH', 'PUT'])
        except ProfileDetails.DoesNotExist:
            if request.method == 'POST':
                data['user'] = request.user.id
                serializer = ProfileDetailsSerializer(data=data)
            else:
                return Response(
                    {'error': 'Profile not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data, 
                status=status.HTTP_200_OK if request.method in ['PUT', 'PATCH'] else status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error in profile_detail view: {str(e)}", exc_info=True)
        return Response(
            {'error': 'An error occurred while processing your request'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )