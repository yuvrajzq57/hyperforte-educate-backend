from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'name', 'password')
        extra_kwargs = {
            'name': {'required': True}
        }
        
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            name=validated_data['name'],
            password=validated_data['password']
        )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user or not user.is_active:
            raise serializers.ValidationError("Incorrect credentials. Please try again.")
        return {'user': user}