from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'favorite-travel-kits', views.FavoriteTravelKitViewSet, basename='favorite-travel-kit')
router.register(r'favorite-items', views.FavoriteTravelKitItemViewSet, basename='favorite-item')

urlpatterns = [
    path('AllLocation/', views.getAllLocation, name='getAllLocation'),
    path('AllTravelKitItems/', views.getAllTravelKitItems, name='getAllTravelKitItems'),
    path('AllTravelKitInfo/', views.getAllTravelKitInfo, name='getAllTravelKitInfo'),
    path('TravelKitInfo/', views.getTravelKitInfo, name='getTravelKitInfo'),
    path('TravelKitItemsByLocation/', views.getTravelKitItemsByLocation, name='getTravelKitItemsByLocation'),
    path('TravelKitItemsByName/', views.getTravelKitItemsByName, name='getTravelKitItemsByName'),
    path('CreateUserTravelKit/', views.createUserTravelKit, name='createUserTravelKit'),
    path('GetUserTravelKit/', views.getUserTravelKit, name='getUserTravelKit'),
    path('DeleteUserTravelKit/<int:kit_id>/', views.deleteUserTravelKit, name='deleteUserTravelKit'),
]