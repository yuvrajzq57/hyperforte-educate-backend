from rest_framework import serializers
from .models import Course, Module, Section, Quiz, Question, QuestionOption

class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ['id', 'option_text', 'is_correct', 'order_number']

class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'order_number', 'created_at', 'options']

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Quiz
        fields = ['id', 'module', 'title', 'passing_score', 'created_at', 'updated_at', 'questions']

class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = [
            'id', 'module', 'title', 'content', 'content_type', 
            'video_url', 'order_number', 'summary', 'created_at', 'updated_at'
        ]

class ModuleSerializer(serializers.ModelSerializer):
    sections = SectionSerializer(many=True, read_only=True)
    quiz = QuizSerializer(read_only=True)
    
    class Meta:
        model = Module
        fields = [
            'id', 'course', 'title', 'description', 'order_number', 
            'image_url', 'created_at', 'updated_at', 'sections', 'quiz'
        ]

class CourseSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'thumbnail_url', 'level',
            'estimated_duration', 'created_at', 'updated_at', 'modules'
        ]
        read_only_fields = ['created_at', 'updated_at']
