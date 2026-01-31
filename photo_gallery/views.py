from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count, Q
from .models import PhotoGallery, PhotoLike
from .serializers import PhotoGallerySerializer, PhotoLikeSerializer


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
            return Response({'status': 'success', 'message': 'Photo unliked', 'is_liked': False, 'likes_count': photo.likes_count})
        except PhotoLike.DoesNotExist:
            PhotoLike.objects.create(photo=photo, user=user)
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
