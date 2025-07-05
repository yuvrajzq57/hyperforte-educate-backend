from rest_framework import serializers
from .models import UserStudyPlan, StudyPlanDay


class StudyPlanDaySerializer(serializers.ModelSerializer):
    """Serializer for StudyPlanDay model."""
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = StudyPlanDay
        fields = ('id', 'day_of_week', 'day_name')
        read_only_fields = ('id', 'day_name')


class UserStudyPlanSerializer(serializers.ModelSerializer):
    """Serializer for UserStudyPlan model."""
    study_days = StudyPlanDaySerializer(many=True, required=False)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    study_days_list = serializers.SerializerMethodField()

    class Meta:
        model = UserStudyPlan
        fields = (
            'id', 'user', 'user_email', 'enabled', 'preferred_time', 
            'reminder_email', 'target_completion_date', 'study_days',
            'study_days_list', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'study_days_list')
        extra_kwargs = {
            'user': {'write_only': True}
        }

    def get_study_days_list(self, obj):
        """Get a list of day names for the study days."""
        return obj.get_study_days_display()

    def create(self, validated_data):
        """Create a new study plan with study days."""
        study_days_data = validated_data.pop('study_days', [])
        study_plan = UserStudyPlan.objects.create(**validated_data)
        
        # Create study days
        for day_data in study_days_data:
            StudyPlanDay.objects.create(study_plan=study_plan, **day_data)
            
        return study_plan

    def update(self, instance, validated_data):
        study_days_data = validated_data.pop('study_days', None)
        
        # Update study plan fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update study days if provided
        if study_days_data is not None:
            # Delete existing study days
            instance.study_days.all().delete()
            
            # Create new study days
            for day_data in study_days_data:
                StudyPlanDay.objects.create(study_plan=instance, **day_data)
        
        return instance
