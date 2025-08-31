import logging
from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()
logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'name', 'is_active', 'date_joined')
        read_only_fields = ('id', 'is_active', 'date_joined')

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    student_external_id = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="External ID for SPOC portal integration"
    )
    
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'name', 'password', 'student_external_id')
        extra_kwargs = {
            'name': {'required': True}
        }
        
    def validate_student_external_id(self, value):
        if value and User.objects.filter(student_external_id=value).exists():
            raise serializers.ValidationError("A user with this external ID already exists.")
        return value
        
    def generate_student_external_id(self, name):
        """Generate a unique student external ID based on name and a number."""
        # Clean the name and create base ID
        base_id = name.lower().replace(' ', '_')
        external_id = f"{base_id}_1"  # Start with _1
        
        # Check if this ID exists and increment the number if it does
        counter = 1
        while User.objects.filter(student_external_id=external_id).exists():
            counter += 1
            external_id = f"{base_id}_{counter}"
            
        return external_id
        
    def create(self, validated_data):
        # Remove student_external_id from validated_data since we'll handle it ourselves
        validated_data.pop('student_external_id', None)
        
        # Create the user first without the student_external_id
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            name=validated_data['name'],
            password=validated_data['password']
        )
        
        # Generate and assign a unique student_external_id
        user.student_external_id = self.generate_student_external_id(validated_data['name'])
        user.save(update_fields=['student_external_id'])
            
        # Log the user creation with external ID for SPOC integration
        logger.info(f"New user created with email: {user.email}, auto-generated external_id: {user.student_external_id}")
        
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