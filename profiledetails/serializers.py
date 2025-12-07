from rest_framework import serializers
from .models import ProfileDetails

class ProfileDetailsSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    join_date = serializers.DateTimeField(source='user.date_joined', read_only=True)
    
    class Meta:
        model = ProfileDetails
        fields = [
            'id', 'username', 'email', 'about', 'background', 
            'student_type', 'preferred_learning_style', 'learning_preference',
            'strengths', 'weaknesses', 'skill_levels', 'learning_goals',
            'created_at', 'updated_at', 'join_date'
        ]
        read_only_fields = ['created_at', 'updated_at', 'join_date']
    
    def to_representation(self, instance):
        """
        Override to include additional user-related fields in the response
        """
        representation = super().to_representation(instance)
        # Add default values for frontend compatibility
        representation['description'] = representation.get('about', '')
        
        # Only set empty arrays if the fields are None or empty
        if not representation.get('strengths'):
            representation['strengths'] = []
            
        if not representation.get('weaknesses'):
            representation['weaknesses'] = []
            
        if not representation.get('learning_goals'):
            representation['learning_goals'] = []
            
        if not representation.get('skill_levels'):
            representation['skill_levels'] = {}
            
        # Add the skill_levels as skillLevels for frontend compatibility
        representation['skillLevels'] = representation.get('skill_levels', {})
        
        # Add learning_goals as learningGoals for frontend compatibility
        representation['learningGoals'] = representation.get('learning_goals', [])
        
        return representation