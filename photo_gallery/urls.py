from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PhotoGalleryViewSet, PublicPhotoViewSet, FavoriteLocationViewSet

# Create a router for the viewset
# This automatically generates URLs for CRUD operations
router = DefaultRouter()
router.register(r'photos', PhotoGalleryViewSet, basename='photo-gallery')
router.register(r'photos/public', PublicPhotoViewSet, basename='public-photos')
router.register(r'favorite-locations', FavoriteLocationViewSet, basename='favorite-location')

urlpatterns = [
    path('', include(router.urls)),
]
