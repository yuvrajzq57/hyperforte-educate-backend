from rest_framework import serializers
from .models import UserModuleProgress, UserSectionProgress, UserQuizAttempt

class UserSectionProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSectionProgress
        fields = ['id', 'section', 'is_completed', 'last_accessed', 'completed_at', 'last_position']
        read_only_fields = ['user', 'last_accessed', 'completed_at']

class UserModuleProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModuleProgress
        fields = ['id', 'module', 'is_completed', 'progress_percentage', 'last_accessed', 'completed_at']
        read_only_fields = ['user', 'progress_percentage', 'last_accessed', 'completed_at']

class UserQuizAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserQuizAttempt
        fields = ['id', 'quiz', 'score', 'passed', 'started_at', 'completed_at', 'time_taken']
        read_only_fields = ['user', 'passed', 'started_at', 'completed_at']

class SectionProgressUpdateSerializer(serializers.Serializer):
    is_completed = serializers.BooleanField(required=False)
    last_position = serializers.FloatField(required=False, min_value=0)

    def update(self, instance, validated_data):
        instance.is_completed = validated_data.get('is_completed', instance.is_completed)
        instance.last_position = validated_data.get('last_position', instance.last_position)
        instance.save()
        return instance

class QuizAttemptCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserQuizAttempt
        fields = ['quiz', 'score', 'time_taken']
        read_only_fields = ['user', 'passed', 'started_at', 'completed_at']

    def create(self, validated_data):
        user = self.context['request'].user
        quiz_attempt = UserQuizAttempt.objects.create(user=user, **validated_data)
        return quiz_attempt
