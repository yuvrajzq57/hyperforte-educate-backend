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
    password = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            raise serializers.ValidationError("Both email and password are required.")
        
        # First try to get the user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "No account found with this email address."})
        
        # Now try to authenticate
        user = authenticate(username=email, password=password)
        
        if not user:
            raise serializers.ValidationError({"password": "Incorrect password."})
            
        if not user.is_active:
            raise serializers.ValidationError({"account": "This account is not active."})
            
        return {'user': user}