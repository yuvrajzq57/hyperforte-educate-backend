from rest_framework import serializers
from .models import ChatMessage, ChatContext

class ChatMessageSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'username', 'module_id', 'message', 'response', 'timestamp']
        read_only_fields = ['response', 'timestamp']
    
    def get_username(self, obj):
        return obj.user.username

class ChatContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatContext
        fields = ['module_id', 'context', 'last_updated']