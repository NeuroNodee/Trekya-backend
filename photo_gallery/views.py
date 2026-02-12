from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import PhotoGallery, PhotoLike, FavoriteLocation
from .serializers import PhotoGallerySerializer, PhotoLikeSerializer, FavoriteLocationSerializer

User = get_user_model()


class PhotoGalleryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PhotoGallery model.
    Provides CRUD operations and custom endpoints for photo management.
    """
    serializer_class = PhotoGallerySerializer
    permission_classes = [IsAuthenticated]  # Only logged-in users can access

    def get_queryset(self):
        """
        Only return photos of the currently logged-in user.
        """
        return PhotoGallery.objects.filter(user=self.request.user).select_related('user')

    def perform_create(self, serializer):
        """
        When creating a photo, automatically attach it to the current user.
        """
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def grouped(self, request):
        """
        GET /api/photos/grouped/
        Returns photos grouped by location.
        """
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({'status':'success','message':'No photos found','data':[]})

        # Group by location
        grouped_data = {}
        for photo in queryset:
            location = photo.get_location_display()
            if location not in grouped_data:
                grouped_data[location] = {'location': location, 'photos': []}
            grouped_data[location]['photos'].append(photo)

        # Serialize
        serialized_groups = []
        for loc, group in grouped_data.items():
            group['photos'] = PhotoGallerySerializer(group['photos'], many=True, context={'request': request}).data
            serialized_groups.append(group)

        return Response({'status':'success','count':queryset.count(),'data':serialized_groups})

    @action(detail=False, methods=['get'])
    def by_location(self, request):
        """
        GET /api/photos/by_location/?location=Kathmandu
        Returns photos filtered by a specific location.
        """
        location = request.query_params.get('location')
        if not location:
            return Response({'status':'error','message':'Location required'}, status=400)

        queryset = self.get_queryset().filter(location=location)
        serializer = self.get_serializer(queryset, many=True)
        return Response({'status':'success','count': queryset.count(),'location': location,'data': serializer.data})

    def list(self, request, *args, **kwargs):
        """
        GET /api/photos/
        List all photos of the authenticated user.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'status':'success','count':queryset.count(),'data':serializer.data})

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """
        POST /api/photos/{id}/like/
        Like/unlike a photo (toggle)
        """
        photo = self.get_object()
        user = request.user
        
        try:
            like = PhotoLike.objects.get(photo=photo, user=user)
            like.delete()
            # Refresh photo to get updated likes_count
            photo.refresh_from_db()
            return Response({'status': 'success', 'message': 'Photo unliked', 'is_liked': False, 'likes_count': photo.likes_count})
        except PhotoLike.DoesNotExist:
            PhotoLike.objects.create(photo=photo, user=user)
            # Refresh photo to get updated likes_count
            photo.refresh_from_db()
            return Response({'status': 'success', 'message': 'Photo liked', 'is_liked': True, 'likes_count': photo.likes_count})


class PublicPhotoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing public photos.
    Allows anyone to view photos from all users that are marked as public (is_public=True).
    Popular endpoint sorts by likes count.
    """
    serializer_class = PhotoGallerySerializer
    permission_classes = [AllowAny]  # Anyone can view
    
    def get_queryset(self):
        """Filter for public photos"""
        return PhotoGallery.objects.filter(is_public=True).select_related('user').prefetch_related('likes')

    @action(detail=False, methods=['get'])
    def by_location(self, request):
        """
        GET /api/photos/public/by_location/?location=Kathmandu
        Returns all public photos filtered by a specific location.
        """
        location = request.query_params.get('location')
        if not location:
            return Response({'status':'error','message':'Location required'}, status=400)

        queryset = self.get_queryset().filter(location=location)
        
        # Pagination support
        page = request.query_params.get('page', 1)
        limit = request.query_params.get('limit', 12)
        
        try:
            page = int(page)
            limit = int(limit)
        except ValueError:
            page = 1
            limit = 12
        
        total_count = queryset.count()
        total_pages = (total_count + limit - 1) // limit
        
        start = (page - 1) * limit
        end = start + limit
        paginated_queryset = queryset[start:end]
        
        serializer = self.get_serializer(paginated_queryset, many=True)
        return Response({
            'status': 'success',
            'count': total_count,
            'page': page,
            'limit': limit,
            'pages': total_pages,
            'location': location,
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        GET /api/photos/public/popular/
        Returns all public photos sorted by likes (most popular first).
        Supports pagination with page and limit query params.
        """
        # Sort by likes count (descending), then by upload date
        queryset = self.get_queryset().annotate(
            like_count=Count('likes')
        ).order_by('-like_count', '-uploaded_at')
        
        # Pagination support
        page = request.query_params.get('page', 1)
        limit = request.query_params.get('limit', 12)
        
        try:
            page = int(page)
            limit = int(limit)
        except ValueError:
            page = 1
            limit = 12
        
        total_count = queryset.count()
        total_pages = (total_count + limit - 1) // limit
        
        start = (page - 1) * limit
        end = start + limit
        paginated_queryset = queryset[start:end]
        
        serializer = self.get_serializer(paginated_queryset, many=True)
        return Response({
            'status': 'success',
            'count': total_count,
            'page': page,
            'limit': limit,
            'pages': total_pages,
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def trending(self, request):
        """
        GET /api/photos/public/trending/
        Returns public photos sorted by date (newest first).
        Can be filtered by location using ?location=LocationName
        """
        queryset = self.get_queryset().order_by('-uploaded_at')
        
        # Filter by location if provided
        location = request.query_params.get('location')
        if location:
            queryset = queryset.filter(location=location)
        
        # Pagination support
        page = request.query_params.get('page', 1)
        limit = request.query_params.get('limit', 12)
        
        try:
            page = int(page)
            limit = int(limit)
        except ValueError:
            page = 1
            limit = 12
        
        total_count = queryset.count()
        total_pages = (total_count + limit - 1) // limit
        
        start = (page - 1) * limit
        end = start + limit
        paginated_queryset = queryset[start:end]
        
        serializer = self.get_serializer(paginated_queryset, many=True)
        return Response({
            'status': 'success',
            'count': total_count,
            'page': page,
            'limit': limit,
            'pages': total_pages,
            'location': location or 'all',
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def grouped(self, request):
        """
        GET /api/photos/public/grouped/
        Returns public photos grouped by location.
        """
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response({'status':'success','message':'No photos found','data':[]})

        # Group by location
        grouped_data = {}
        for photo in queryset:
            location = photo.get_location_display()
            if location not in grouped_data:
                grouped_data[location] = {'location': location, 'photos': [], 'count': 0}
            grouped_data[location]['photos'].append(photo)
            grouped_data[location]['count'] += 1

        # Serialize - limit to 6 photos per location for preview
        serialized_groups = []
        for loc, group in sorted(grouped_data.items()):
            photos_preview = group['photos'][:6]
            group['photos'] = PhotoGallerySerializer(photos_preview, many=True, context={'request': request}).data
            serialized_groups.append({
                'location': group['location'],
                'count': group['count'],
                'photos': group['photos']
            })

        return Response({
            'status': 'success',
            'total_photos': queryset.count(),
            'data': serialized_groups
        })

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """
        POST /api/photos/public/{id}/like/
        Like/unlike a public photo (toggle)
        Requires authentication.
        """
        photo = self.get_object()
        user = request.user
        
        try:
            like = PhotoLike.objects.get(photo=photo, user=user)
            like.delete()
            # Refresh photo to get updated likes_count
            photo.refresh_from_db()
            return Response({'status': 'success', 'message': 'Photo unliked', 'is_liked': False, 'likes_count': photo.likes_count})
        except PhotoLike.DoesNotExist:
            PhotoLike.objects.create(photo=photo, user=user)
            # Refresh photo to get updated likes_count
            photo.refresh_from_db()
            return Response({'status': 'success', 'message': 'Photo liked', 'is_liked': True, 'likes_count': photo.likes_count})

class FavoriteLocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing favorite destinations/locations.
    
    Endpoints:
    - GET /api/favorite-locations/ - List user's favorite locations
    - POST /api/favorite-locations/ - Add a favorite location
    - DELETE /api/favorite-locations/{id}/ - Remove a favorite location
    - POST /api/favorite-locations/toggle/ - Toggle favorite location
    - GET /api/favorite-locations/check/ - Check if location is favorited
    """
    serializer_class = FavoriteLocationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter favorites for the authenticated user only"""
        return FavoriteLocation.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        """Automatically set the user to the current logged-in user"""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """
        Toggle favorite location.
        POST /api/favorite-locations/toggle/
        
        Request body:
        {
            "location": "Kathmandu"
        }
        """
        location = request.data.get('location')
        
        if not location:
            return Response(
                {'status': 'error', 'error': 'location is required', 'valid_locations': [choice[0] for choice in FavoriteLocation.LOCATION_CHOICES]},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate location is in LOCATION_CHOICES
        valid_locations = [choice[0] for choice in FavoriteLocation.LOCATION_CHOICES]
        if location not in valid_locations:
            return Response(
                {'status': 'error', 'error': f'Invalid location. Must be one of: {valid_locations}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Try to find and delete existing favorite
            favorite = FavoriteLocation.objects.get(
                user=request.user,
                location=location
            )
            favorite.delete()
            return Response({
                'status': 'success',
                'is_favorited': False,
                'location': location,
                'message': 'Removed from favorites'
            }, status=status.HTTP_200_OK)
        except FavoriteLocation.DoesNotExist:
            # Create new favorite
            try:
                FavoriteLocation.objects.create(
                    user=request.user,
                    location=location
                )
                return Response({
                    'status': 'success',
                    'is_favorited': True,
                    'location': location,
                    'message': 'Added to favorites'
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    'status': 'error',
                    'error': f'Error adding favorite: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def check(self, request):
        """
        Check if a location is in user's favorites.
        GET /api/favorite-locations/check/?location=Kathmandu
        """
        location = request.query_params.get('location')
        
        if not location:
            return Response(
                {'status': 'error', 'error': 'location is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        is_favorited = FavoriteLocation.objects.filter(
            user=request.user,
            location=location
        ).exists()
        
        return Response({
            'status': 'success',
            'location': location,
            'is_favorited': is_favorited
        }, status=status.HTTP_200_OK)


# =====================================================
# USER-SPECIFIC PHOTO GALLERY ENDPOINT (AS PER SPEC)
# =====================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def user_photo_gallery(request, user_id):
    """
    GET /api/photo-gallery/<user_id>/
    
    Returns list of photos for a specific user.
    This endpoint matches the requirement specification exactly:
    - Accepts user_id parameter
    - Returns list of photos with image URL and location
    - Returns empty list if no photos are found
    - Handles invalid user_id gracefully
    
    Response format:
    {
        "status": "success",
        "message": "Photos retrieved successfully",
        "count": 5,
        "user_id": 1,
        "data": [
            {
                "id": 1,
                "image_url": "http://...",
                "location": "Kathmandu",
                "title": "...",
                "uploaded_at": "..."
            },
            ...
        ]
    }
    """
    try:
        # Validate that user_id is a valid integer
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return Response({
                'status': 'error',
                'message': 'Invalid user_id. Must be an integer.',
                'count': 0,
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user exists
        user = get_object_or_404(User, id=user_id)
        
        # Get all photos for this user (only public photos for non-authenticated users)
        if request.user.is_authenticated and request.user.id == user_id:
            # Authenticated users can see all their own photos
            photos = PhotoGallery.objects.filter(user=user).select_related('user').order_by('-uploaded_at')
        else:
            # Non-authenticated users or other authenticated users see only public photos
            photos = PhotoGallery.objects.filter(user=user, is_public=True).select_related('user').order_by('-uploaded_at')
        
        # Serialize the photos
        serializer = PhotoGallerySerializer(photos, many=True, context={'request': request})
        
        return Response({
            'status': 'success',
            'message': 'Photos retrieved successfully' if photos.exists() else 'No photos found for this user',
            'count': photos.count(),
            'user_id': user_id,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Error retrieving photos: {str(e)}',
            'count': 0,
            'data': []
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)