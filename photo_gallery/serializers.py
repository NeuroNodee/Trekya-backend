from rest_framework import serializers
from .models import PhotoGallery, PhotoLike, FavoriteLocation

class PhotoGallerySerializer(serializers.ModelSerializer):
    """
    Serializer for photogallery model. 
    convert photogallery model instances to JSON and vice versa. 
    Used for API responses and validation. 
    """

    #read only field to show user email instead of ID
    user_email = serializers.CharField(source='user.email', read_only=True)
    uploaded_by = serializers.SerializerMethodField()
    user_first_name = serializers.CharField(source='user.first_name', read_only=True)
    user_last_name = serializers.CharField(source='user.last_name', read_only=True)
    image_url = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = PhotoGallery
        fields = ['id', 'user_email', 'uploaded_by', 'user_first_name', 'user_last_name', 'image', 'image_url', 'location', 'title', 'description', 'is_public', 'likes_count', 'is_liked', 'uploaded_at']
        read_only_fields = ['id', 'user_email', 'uploaded_by', 'user_first_name', 'user_last_name', 'likes_count', 'is_liked', 'uploaded_at']

    def get_uploaded_by(self, obj):
        """Get uploader's full name or email"""
        if obj.user.first_name and obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
        elif obj.user.first_name:
            return obj.user.first_name
        else:
            return obj.user.email

    def get_image_url(self, obj):
        """
        Method to get the full image URL.
        The request context is required to build absolute URLs.
        """
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None

    def get_likes_count(self, obj):
        """Get total likes count for this photo"""
        return obj.likes_count

    def get_is_liked(self, obj):
        """Check if current user has liked this photo"""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.is_liked_by(request.user)
        return False

    def validate_image(self, value):
        """
        Validate image file size (max 5MB)
        """
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError("Image size must not exceed 5MB.")
        return value


class PhotoLikeSerializer(serializers.ModelSerializer):
    """Serializer for PhotoLike model"""
    class Meta:
        model = PhotoLike
        fields = ['id', 'photo', 'user', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class PhotoGalleryGroupedSerializer(serializers.Serializer):
    location = serializers.CharField()
    photos = PhotoGallerySerializer(many=True)
    count = serializers.SerializerMethodField()

    def get_count(self, obj):
        return len(obj['photos'])

class FavoriteLocationSerializer(serializers.ModelSerializer):
    """
    Serializer for FavoriteLocation model - tracks user's favorite destinations
    """
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = FavoriteLocation
        fields = ['id', 'user_email', 'location', 'created_at']
        read_only_fields = ['id', 'user_email', 'created_at']