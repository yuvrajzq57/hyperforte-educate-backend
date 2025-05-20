from rest_framework import serializers
from .models import ProfileDetails

class ProfileDetailsSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ProfileDetails
        fields = ['id', 'username', 'about', 'background', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']