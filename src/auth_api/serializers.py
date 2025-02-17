# src/auth_api/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile




class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ('email', 'password', 'confirm_password', 'first_name', 'last_name')

    def validate(self, attrs):
        # Remove confirm_password from attrs after validation
        if attrs['password'] != attrs.pop('confirm_password'):
            raise serializers.ValidationError({
                "password": "Password fields do not match."
            })
        
        # Check email uniqueness
        email = attrs.get('email')
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({
                "email": "User with this email already exists."
            })
            
        return attrs

    def create(self, validated_data):
        email = validated_data['email']
        
        # Create user with email as username
        user = User.objects.create_user(
            username=email,  # Use email as username
            email=email,
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        
        # Create the user profile
        UserProfile.objects.create(user=user)
        
        return user
        

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('email', 'first_name', 'last_name', 'last_login', 'account_created')

    def to_representation(self, instance):
        # Get user data and combine with profile data
        data = super().to_representation(instance)
        data['email'] = instance.user.email
        data['first_name'] = instance.user.first_name
        data['last_name'] = instance.user.last_name
        return data

class SocialAuthSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    provider = serializers.CharField() 

    

class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_new_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError({
                "new_password": "Password fields do not match."
            })
        return attrs

class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    email = serializers.EmailField(required=True)

class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                "new_password": "Password fields do not match."
            })
        return attrs



class TokenResponseSerializer(serializers.Serializer):
    """Serializer for token response"""
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    token_type = serializers.CharField(default='Bearer')
    expires_in = serializers.IntegerField()
    user = UserProfileSerializer(read_only=True)

    class Meta:
        fields = ('access_token', 'refresh_token', 'token_type', 'expires_in', 'user')


class TokenRefreshSerializer(serializers.Serializer):
    """Serializer for token refresh"""
    refresh_token = serializers.CharField(required=True)