from django.shortcuts import render
from .models import Location, TravelKitItem, TravelKit, FavoriteTravelKit, FavoriteTravelKitItem
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import viewsets, status
from .serializers import FavoriteTravelKitSerializer, FavoriteTravelKitItemSerializer

# Create your views here.
@api_view(['GET'])
@permission_classes([AllowAny])
def getAllLocation(request):
    """Get all locations"""
    locations = Location.objects.all().values()
    return Response({ "message": "Success", "data": list(locations) })

@api_view(['GET'])
@permission_classes([AllowAny])
def getAllTravelKitItems(request):
    """Get all travel kit items"""
    travel_kits = TravelKitItem.objects.all().values()
    return Response({ "message": "Success", "data": list(travel_kits) })


@api_view(['GET'])
@permission_classes([AllowAny])
def getAllTravelKitInfo(request):
    """Get all travel kit info"""
    travel_kits = TravelKit.objects.all().values()
    return Response({ "message": "Success", "data": list(travel_kits) })

@api_view(['GET'])
@permission_classes([AllowAny])
def getTravelKitInfo(request):
    """Get specific travel kit info by location"""
    location = request.GET.get('location')
    if not location:
        return Response({ "message": "Location is required" })
    travel_kit = TravelKit.objects.filter(locations__name=location).values()
    return Response({ "message": "Success", "data": list(travel_kit) })

@api_view(['GET'])
@permission_classes([AllowAny])
def getTravelKitItemsByLocation(request):
    """Get specific travel kit items by location, returns list of item in nested dictionary"""
    location = request.GET.get('location')
    if not location:
        return Response({ "message": "Location is required" })
    travel_kit = TravelKit.objects.filter(locations__name=location).first()
    if not travel_kit:
        return Response({ "message": "Travel kit not found" })
    travel_kit_items = travel_kit.items.values()
    return Response({ "message": "Success", "data": list(travel_kit_items) })


class FavoriteTravelKitViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing favorite TravelKits.
    
    Endpoints:
    - GET /api/favorite-travel-kits/ - List user's favorite travel kits
    - POST /api/favorite-travel-kits/ - Add a favorite travel kit
    - DELETE /api/favorite-travel-kits/{id}/ - Remove a favorite travel kit
    - POST /api/favorite-travel-kits/toggle/ - Toggle favorite travel kit
    - GET /api/favorite-travel-kits/check/ - Check if travel kit is favorited
    """
    serializer_class = FavoriteTravelKitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter favorites for the authenticated user only"""
        return FavoriteTravelKit.objects.filter(user=self.request.user).select_related('travel_kit').order_by('-created_at')

    def perform_create(self, serializer):
        """Automatically set the user to the current logged-in user"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """
        Toggle favorite travel kit.
        POST /api/favorite-travel-kits/toggle/
        
        Request body:
        {
            "travel_kit": 1
        }
        """
        travel_kit_id = request.data.get('travel_kit')
        
        if not travel_kit_id:
            return Response(
                {'error': 'travel_kit is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify travel kit exists
        try:
            travel_kit = TravelKit.objects.get(id=travel_kit_id)
        except TravelKit.DoesNotExist:
            return Response(
                {'error': 'Travel kit not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Try to find and delete existing favorite
            favorite = FavoriteTravelKit.objects.get(
                user=request.user,
                travel_kit=travel_kit
            )
            favorite.delete()
            return Response({
                'is_favorited': False,
                'travel_kit_id': travel_kit_id,
                'message': 'Removed from favorites'
            }, status=status.HTTP_200_OK)
        except FavoriteTravelKit.DoesNotExist:
            # Create new favorite
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response({
                'is_favorited': True,
                'travel_kit_id': travel_kit_id,
                'message': 'Added to favorites',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def check(self, request):
        """
        Check if a travel kit is in user's favorites.
        GET /api/favorite-travel-kits/check/?travel_kit_id=1
        """
        travel_kit_id = request.query_params.get('travel_kit_id')
        
        if not travel_kit_id:
            return Response(
                {'error': 'travel_kit_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        is_favorited = FavoriteTravelKit.objects.filter(
            user=request.user,
            travel_kit_id=travel_kit_id
        ).exists()
        
        return Response({
            'travel_kit_id': travel_kit_id,
            'is_favorited': is_favorited
        }, status=status.HTTP_200_OK)


class FavoriteTravelKitItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing favorite TravelKit Items (for wishlist/shopping).
    
    Endpoints:
    - GET /api/favorite-items/ - List user's favorite items
    - POST /api/favorite-items/ - Add a favorite item
    - DELETE /api/favorite-items/{id}/ - Remove a favorite item
    - POST /api/favorite-items/toggle/ - Toggle favorite item
    - GET /api/favorite-items/check/ - Check if item is favorited
    """
    serializer_class = FavoriteTravelKitItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter favorites for the authenticated user only"""
        return FavoriteTravelKitItem.objects.filter(user=self.request.user).select_related('item').order_by('-created_at')

    def perform_create(self, serializer):
        """Automatically set the user to the current logged-in user"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """
        Toggle favorite travel kit item.
        POST /api/favorite-items/toggle/
        
        Request body:
        {
            "item": 1
        }
        """
        item_id = request.data.get('item')
        
        if not item_id:
            return Response(
                {'error': 'item is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify item exists
        try:
            item = TravelKitItem.objects.get(id=item_id)
        except TravelKitItem.DoesNotExist:
            return Response(
                {'error': 'Item not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Try to find and delete existing favorite
            favorite = FavoriteTravelKitItem.objects.get(
                user=request.user,
                item=item
            )
            favorite.delete()
            return Response({
                'is_favorited': False,
                'item_id': item_id,
                'message': 'Removed from favorites'
            }, status=status.HTTP_200_OK)
        except FavoriteTravelKitItem.DoesNotExist:
            # Create new favorite
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response({
                'is_favorited': True,
                'item_id': item_id,
                'message': 'Added to favorites',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def check(self, request):
        """
        Check if an item is in user's favorites.
        GET /api/favorite-items/check/?item_id=1
        """
        item_id = request.query_params.get('item_id')
        
        if not item_id:
            return Response(
                {'error': 'item_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        is_favorited = FavoriteTravelKitItem.objects.filter(
            user=request.user,
            item_id=item_id
        ).exists()
        
        return Response({
            'item_id': item_id,
            'is_favorited': is_favorited
        }, status=status.HTTP_200_OK)
