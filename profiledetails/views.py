from django.shortcuts import render, get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ProfileDetails
from .serializers import ProfileDetailsSerializer

@api_view(['GET', 'POST', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile_detail(request):
    """
    Handle profile details with support for GET, POST, PUT, and PATCH methods.
    """
    try:
        profile = ProfileDetails.objects.get(user=request.user)
    except ProfileDetails.DoesNotExist:
        # Create an empty profile if it doesn't exist
        profile = None

    if request.method == 'GET':
        if profile:
            serializer = ProfileDetailsSerializer(profile)
            return Response(serializer.data)
        return Response({
            'message': 'Profile not found',
            'username': request.user.username,
            'email': request.user.email,
            'join_date': request.user.date_joined
        }, status=status.HTTP_404_NOT_FOUND)

    elif request.method in ['POST', 'PUT', 'PATCH']:
        # Handle both create and update operations
        data = request.data.copy()
        
        # Map description to about for frontend compatibility
        if 'description' in data and 'about' not in data:
            data['about'] = data['description']
            
        if profile:
            # Update existing profile
            serializer = ProfileDetailsSerializer(profile, data=data, partial=request.method == 'PATCH')
        else:
            # Create new profile
            serializer = ProfileDetailsSerializer(data=data)
        
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, 
                         status=status.HTTP_200_OK if profile else status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(
        {'error': 'Method not allowed'}, 
        status=status.HTTP_405_METHOD_NOT_ALLOWED
    )