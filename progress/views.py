from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404, ListAPIView
from django.db.models import Prefetch
from courses.models import Module, Section, Quiz
from .models import UserModuleProgress, UserSectionProgress, UserQuizAttempt
from .serializers import (
    UserModuleProgressSerializer, 
    UserSectionProgressSerializer,
    UserQuizAttemptSerializer,
    SectionProgressUpdateSerializer,
    QuizAttemptCreateSerializer
)

class ModuleProgressListView(ListAPIView):
    """
    API endpoint that allows users to view their progress for all modules in a course.
    """
    serializer_class = UserModuleProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        course_id = self.kwargs.get('course_id')
        return UserModuleProgress.objects.filter(
            user=self.request.user,
            module__course_id=course_id
        ).select_related('module')

class SectionProgressView(APIView):
    """
    API endpoint for getting and updating section progress.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, section_id):
        progress, created = UserSectionProgress.objects.get_or_create(
            user=request.user,
            section_id=section_id
        )
        serializer = UserSectionProgressSerializer(progress)
        return Response(serializer.data)

    def patch(self, request, section_id):
        progress = get_object_or_404(
            UserSectionProgress,
            user=request.user,
            section_id=section_id
        )
        serializer = SectionProgressUpdateSerializer(
            progress,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QuizAttemptView(APIView):
    """
    API endpoint for creating and listing quiz attempts.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, quiz_id):
        attempts = UserQuizAttempt.objects.filter(
            user=request.user,
            quiz_id=quiz_id
        ).order_by('-completed_at')
        serializer = UserQuizAttemptSerializer(attempts, many=True)
        return Response(serializer.data)

    def post(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        serializer = QuizAttemptCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            # Ensure the quiz ID in the URL matches the one in the request
            if serializer.validated_data['quiz'] != quiz:
                return Response(
                    {"error": "Quiz ID in URL does not match the quiz in the request"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            quiz_attempt = serializer.save()
            return Response(
                UserQuizAttemptSerializer(quiz_attempt).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProgressOverview(APIView):
    """
    API endpoint to get an overview of user's progress across all courses.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get all modules with progress for the user
        modules_progress = UserModuleProgress.objects.filter(
            user=request.user
        ).select_related('module__course')
        
        # Group by course
        courses = {}
        for progress in modules_progress:
            course = progress.module.course
            if course.id not in courses:
                courses[course.id] = {
                    'id': course.id,
                    'title': course.title,
                    'total_modules': 0,
                    'completed_modules': 0,
                    'progress_percentage': 0,
                    'modules': []
                }
            
            courses[course.id]['total_modules'] += 1
            if progress.is_completed:
                courses[course.id]['completed_modules'] += 1
            
            courses[course.id]['modules'].append({
                'id': progress.module.id,
                'title': progress.module.title,
                'is_completed': progress.is_completed,
                'progress_percentage': progress.progress_percentage,
                'last_accessed': progress.last_accessed
            })
        
        # Calculate overall progress for each course
        for course_id in courses:
            if courses[course_id]['total_modules'] > 0:
                courses[course_id]['progress_percentage'] = (
                    courses[course_id]['completed_modules'] / 
                    courses[course_id]['total_modules'] * 100
                )
        
        return Response({
            'courses': list(courses.values())
        })
