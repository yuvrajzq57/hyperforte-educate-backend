from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from django.utils import timezone
from django.db import transaction

from .models import UserStudyPlan, StudyPlanDay
from .serializers import UserStudyPlanSerializer


class UserStudyPlanView(APIView):
    """
    API endpoint for managing a user's study plan.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Retrieve the user's study plan."""
        try:
            study_plan = UserStudyPlan.objects.get(user=request.user)
        except UserStudyPlan.DoesNotExist:
            return Response(
                {"detail": "Study plan not found. Create one first."},
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = UserStudyPlanSerializer(study_plan)
        return Response(serializer.data)

    @transaction.atomic
    def post(self, request):
        """Create a new study plan for the user."""
        # Check if user already has a study plan
        if UserStudyPlan.objects.filter(user=request.user).exists():
            return Response(
                {"detail": "A study plan already exists for this user. Use PUT to update it."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        data = request.data.copy()
        data['user'] = request.user.id
        
        serializer = UserStudyPlanSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def put(self, request):
        """Update the user's study plan."""
        try:
            study_plan = UserStudyPlan.objects.get(user=request.user)
        except UserStudyPlan.DoesNotExist:
            return Response(
                {"detail": "Study plan not found. Create one first."},
                status=status.HTTP_404_NOT_FOUND
            )
            
        data = request.data.copy()
        data['user'] = request.user.id
        
        serializer = UserStudyPlanSerializer(study_plan, data=data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def patch(self, request):
        """Partially update the user's study plan."""
        try:
            study_plan = UserStudyPlan.objects.get(user=request.user)
        except UserStudyPlan.DoesNotExist:
            return Response(
                {"detail": "Study plan not found. Create one first."},
                status=status.HTTP_404_NOT_FOUND
            )
            
        serializer = UserStudyPlanSerializer(study_plan, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Delete the user's study plan."""
        try:
            study_plan = UserStudyPlan.objects.get(user=request.user)
        except UserStudyPlan.DoesNotExist:
            return Response(
                {"detail": "No study plan found to delete."},
                status=status.HTTP_404_NOT_FOUND
            )
            
        study_plan.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StudyPlanStatusView(APIView):
    """
    API endpoint for checking study plan status and getting today's study session.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get the user's study plan status and today's study session."""
        try:
            study_plan = UserStudyPlan.objects.get(user=request.user)
        except UserStudyPlan.DoesNotExist:
            return Response(
                {
                    "has_study_plan": False,
                    "message": "No study plan found. Create one to get started."
                },
                status=status.HTTP_200_OK
            )
        
        # Get today's day of week (0=Sunday, 6=Saturday)
        today = timezone.now().weekday()
        
        # Check if today is a study day
        is_study_day = study_plan.study_days.filter(day_of_week=today).exists()
        
        response_data = {
            "has_study_plan": True,
            "is_enabled": study_plan.enabled,
            "is_study_day_today": is_study_day,
            "preferred_time": study_plan.preferred_time,
            "reminder_enabled": study_plan.reminder_email,
            "target_completion_date": study_plan.target_completion_date,
            "study_days": [day.get_day_of_week_display() for day in study_plan.study_days.all()]
        }
        
        return Response(response_data)
