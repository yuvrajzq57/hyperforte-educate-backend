# Create your views here.

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Course, Module, Section, Quiz, Question, QuestionOption
from .serializers import (
    CourseSerializer, ModuleSerializer, SectionSerializer,
    QuizSerializer, QuestionSerializer, QuestionOptionSerializer
)

class CourseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows courses to be viewed or edited.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['level']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'created_at', 'updated_at']
    ordering = ['title']

    @action(detail=True, methods=['get'])
    def modules(self, request, pk=None):
        """
        Get all modules for a specific course
        """
        course = self.get_object()
        modules = course.modules.all().order_by('order_number')
        serializer = ModuleSerializer(modules, many=True, context={'request': request})
        return Response(serializer.data)

class ModuleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows modules to be viewed or edited.
    """
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['course']
    ordering_fields = ['order_number', 'title']
    ordering = ['order_number']

    @action(detail=True, methods=['get'])
    def sections(self, request, pk=None):
        """
        Get all sections for a specific module
        """
        module = self.get_object()
        sections = module.sections.all().order_by('order_number')
        serializer = SectionSerializer(sections, many=True, context={'request': request})
        return Response(serializer.data)

class SectionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows sections to be viewed or edited.
    """
    queryset = Section.objects.all()
    serializer_class = SectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['module', 'content_type']
    ordering_fields = ['order_number', 'title']
    ordering = ['order_number']

class QuizViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows quizzes to be viewed or edited.
    """
    queryset = Quiz.objects.all()
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['module']

    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """
        Get all questions for a specific quiz
        """
        quiz = self.get_object()
        questions = quiz.questions.all().order_by('order_number')
        serializer = QuestionSerializer(questions, many=True, context={'request': request})
        return Response(serializer.data)

class QuestionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows questions to be viewed or edited.
    """
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['quiz']
    ordering_fields = ['order_number']
    ordering = ['order_number']

    @action(detail=True, methods=['get'])
    def options(self, request, pk=None):
        """
        Get all options for a specific question
        """
        question = self.get_object()
        options = question.options.all().order_by('order_number')
        serializer = QuestionOptionSerializer(options, many=True, context={'request': request})
        return Response(serializer.data)

class QuestionOptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows question options to be viewed or edited.
    """
    queryset = QuestionOption.objects.all()
    serializer_class = QuestionOptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['question']
    ordering_fields = ['order_number']
    ordering = ['order_number']
