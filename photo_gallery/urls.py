from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PhotoGalleryViewSet, PublicPhotoViewSet, FavoriteLocationViewSet, user_photo_gallery

# Create a router for the viewsets
# This automatically generates URLs for CRUD operations
router = DefaultRouter()
router.register(r'photos', PhotoGalleryViewSet, basename='photo-gallery')
router.register(r'photos/public', PublicPhotoViewSet, basename='public-photos')
router.register(r'favorite-locations', FavoriteLocationViewSet, basename='favorite-location')

urlpatterns = [
    # Auto-generated routes from router
    path('', include(router.urls)),
    
    # USER-SPECIFIC PHOTO GALLERY ENDPOINT (As per specification)
    # GET /api/photo-gallery/<user_id>/
    # Returns list of photos for a specific user with image URL and location
    path('photo-gallery/<int:user_id>/', user_photo_gallery, name='user-photo-gallery'),
]