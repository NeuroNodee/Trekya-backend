from rest_framework import serializers
from .models import PhotoGallery

class PhotoGallerySerializer(serializers.ModelSerializer):
    """
    Serializer for photogallery model. 
    convert photogallery model instances to JSON and vice versa. 
    Used for API responses and validation. 
    """

    #read only field to show user email instead of ID
    user_email = serializers.CharField(source='user.email', read_only=True)
    uploaded_by = serializers.CharField(source='user.username', read_only=True)
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = PhotoGallery
        fields = ['id', 'user_email', 'uploaded_by', 'image', 'image_url', 'location', 'title', 'description', 'is_public', 'uploaded_at']
        read_only_fields = ['id', 'user_email', 'uploaded_by', 'uploaded_at']

    def get_image_url(self, obj):
        """
        Method to get the full image URL.
        The request context is required to build absolute URLs.
        """
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None

    def validate_image(self, value):
        """
        Validate image file size (max 5MB)
        """
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError("Image size must not exceed 5MB.")
        return value


class PhotoGalleryGroupedSerializer(serializers.Serializer):
    location = serializers.CharField()
    photos = PhotoGallerySerializer(many=True)
    count = serializers.SerializerMethodField()

    def get_count(self, obj):
        return len(obj['photos'])
