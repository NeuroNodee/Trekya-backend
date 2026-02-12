from rest_framework import serializers 
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from dj_rest_auth.registration.serializers import RegisterSerializer as BaseRegisterSerializer

User = get_user_model()

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model - used for displaying user info
    """
    remove_profile_picture = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'is_from_nepal', 'profile_picture', 'bio', 'date_joined', 'remove_profile_picture')
        read_only_fields = ('id', 'date_joined', 'email') # Email usually read-only unless we want to handle verification again

    def update(self, instance, validated_data):
        remove_pic = validated_data.pop('remove_profile_picture', False)
        if remove_pic:
            instance.profile_picture.delete(save=False)
            instance.profile_picture = None
        
        return super().update(instance, validated_data)


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration (for our custom endpoint)
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="This email is already registered")]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    full_name = serializers.CharField(required=True, write_only=True)  # <-- add this
    is_from_nepal = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = User
        fields = ('email', 'password', 'full_name', 'is_from_nepal')

    def create(self, validated_data):
        # 1. Extract full_name safely
        full_name = validated_data.pop('full_name')

        # 2. Split into first and last name
        name_parts = full_name.strip().split()
        first_name = name_parts[0] if len(name_parts) > 0 else ''
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

        # 3. Create user
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=first_name,
            last_name=last_name,
            is_from_nepal=validated_data.get('is_from_nepal', False)
        )
        return user



class CustomRegisterSerializer(BaseRegisterSerializer):
    """
    Custom registration serializer for django-allauth (for social auth)
    Extends dj-rest-auth's RegisterSerializer to add our custom field
    """
    is_from_nepal = serializers.BooleanField(required=False, default=False)

    def get_cleaned_data(self):
        """
        Return cleaned data with our custom field
        """
        data = super().get_cleaned_data()
        data['is_from_nepal'] = self.validated_data.get('is_from_nepal', False)
        return data

    def custom_signup(self, request, user):
        """
        Save custom fields during signup (called by allauth)
        """
        user.is_from_nepal = self.validated_data.get('is_from_nepal', False)
        user.save()

    
class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type':'password'}
    )
    remember_me = serializers.BooleanField(required=False, default=False)


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)

    def validate(self, data):
        # Add OTP validation logic here
        if not validate_otp(data['email'], data['otp']):
            raise serializers.ValidationError({'otp': 'Invalid or expired OTP'})
        return data
