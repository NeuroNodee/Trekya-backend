from rest_framework import serializers
from .models import TravelKit, TravelKitItem, FavoriteTravelKit, FavoriteTravelKitItem, Location


class LocationSerializer(serializers.ModelSerializer):
    """Serializer for Location model"""
    class Meta:
        model = Location
        fields = ['id', 'name', 'country']


class TravelKitItemSerializer(serializers.ModelSerializer):
    """Serializer for TravelKitItem model"""
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TravelKitItem
        fields = ['id', 'name', 'category', 'description', 'image', 'image_url', 'price', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_image_url(self, obj):
        """Get the full image URL"""
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None


class TravelKitSerializer(serializers.ModelSerializer):
    """Serializer for TravelKit model"""
    locations = LocationSerializer(many=True, read_only=True)
    items = TravelKitItemSerializer(many=True, read_only=True)
    location_ids = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        many=True,
        write_only=True,
        source='locations'
    )
    item_ids = serializers.PrimaryKeyRelatedField(
        queryset=TravelKitItem.objects.all(),
        many=True,
        write_only=True,
        source='items'
    )
    
    class Meta:
        model = TravelKit
        fields = ['id', 'name', 'description', 'locations', 'location_ids', 'items', 'item_ids', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class FavoriteTravelKitSerializer(serializers.ModelSerializer):
    """Serializer for FavoriteTravelKit model"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    travel_kit_name = serializers.CharField(source='travel_kit.name', read_only=True)
    travel_kit_details = TravelKitSerializer(source='travel_kit', read_only=True)
    
    class Meta:
        model = FavoriteTravelKit
        fields = ['id', 'user_email', 'travel_kit', 'travel_kit_name', 'travel_kit_details', 'created_at']
        read_only_fields = ['id', 'user_email', 'created_at']


class FavoriteTravelKitItemSerializer(serializers.ModelSerializer):
    """Serializer for FavoriteTravelKitItem model"""
    user_email = serializers.CharField(source='user.email', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_details = TravelKitItemSerializer(source='item', read_only=True)
    
    class Meta:
        model = FavoriteTravelKitItem
        fields = ['id', 'user_email', 'item', 'item_name', 'item_details', 'created_at']
        read_only_fields = ['id', 'user_email', 'created_at']
