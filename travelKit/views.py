from django.shortcuts import render
from .models import Location, TravelKitItem, TravelKit, UserPersonalizedTravelKit
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
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

@api_view(['GET'])
@permission_classes([AllowAny])
def getTravelKitItemsByName(request):
    name = request.GET.get('name')

    if not name:
        return Response(
            {"message": "Name is required"},
            status=400
        )

    travel_kit_items = TravelKitItem.objects.filter(
        name__icontains=name
    )

    if not travel_kit_items.exists():
        return Response(
            {"message": "Travel kit item not found"},
            status=404
        )

    return Response(
        {
            "message": "Success",
            "data": travel_kit_items.values()
        },
        status=200
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def createUserTravelKit(request):
    """Create user travel kit"""
    location = request.data.get('location')
    items = request.data.get('items')
    if not location or not items:
        return Response({ "message": "Location and items are required" })
    
    try:
        user_travel_kit, created = UserPersonalizedTravelKit.objects.update_or_create(
            user=request.user,
            location=Location.objects.get(name=location),
            
            defaults={
                'selected_items': items,
                'is_confirmed': True,
                'confirmed_at': timezone.now(),
            }
        )
        if created:
            return Response({ "message": "User travel kit created successfully" })
        else:
            return Response({ "message": "User travel kit updated successfully" })
    except Exception as e:
        return Response({ "message": str(e) })

    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getUserTravelKit(request):
    """Get user travel kit"""
    user_travel_kit = UserPersonalizedTravelKit.objects.filter(user=request.user)
    data = user_travel_kit.values(
        "id",
        "location__name",
        "selected_items",
    )
    if not user_travel_kit:
        return Response({ "message": "User travel kit not found", "data": [] })
    return Response({ "message": "Success", "data": data})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def deleteUserTravelKit(request, kit_id):
    travel_kit = get_object_or_404(
        UserPersonalizedTravelKit,
        id=kit_id,
        user=request.user
    )
    travel_kit.delete()

    return Response(
        {
            "message": "Travel kit deleted successfully",
            "deleted_kit_id": kit_id,
            "location": travel_kit.location.name if travel_kit.location else None
        },
        status=200
    )