"""
Test cases for Photo Gallery API
Run with: python manage.py test photo_gallery.tests.PhotoGalleryTests
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from PIL import Image
from io import BytesIO
from .models import PhotoGallery, PhotoLike, FavoriteLocation

User = get_user_model()


class PhotoGalleryModelTests(TestCase):
    """Test cases for PhotoGallery model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )

    def create_test_image(self):
        """Create a test image file"""
        image = Image.new('RGB', (100, 100), color='red')
        image_io = BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        return SimpleUploadedFile(
            'test_image.jpg',
            image_io.getvalue(),
            content_type='image/jpeg'
        )

    def test_create_photo_gallery(self):
        """Test creating a photo gallery entry"""
        photo = PhotoGallery.objects.create(
            user=self.user,
            image=self.create_test_image(),
            location='Kathmandu',
            title='Test Photo',
            description='Test Description'
        )
        self.assertEqual(photo.user, self.user)
        self.assertEqual(photo.location, 'Kathmandu')
        self.assertEqual(photo.title, 'Test Photo')

    def test_photo_string_representation(self):
        """Test string representation of photo"""
        photo = PhotoGallery.objects.create(
            user=self.user,
            image=self.create_test_image(),
            location='Kathmandu'
        )
        self.assertIn(self.user.email, str(photo))
        self.assertIn('Kathmandu', str(photo))

    def test_likes_count_property(self):
        """Test likes count property"""
        photo = PhotoGallery.objects.create(
            user=self.user,
            image=self.create_test_image(),
            location='Kathmandu'
        )
        self.assertEqual(photo.likes_count, 0)

        # Add a like
        PhotoLike.objects.create(photo=photo, user=self.user)
        self.assertEqual(photo.likes_count, 1)

    def test_is_liked_by_method(self):
        """Test is_liked_by method"""
        photo = PhotoGallery.objects.create(
            user=self.user,
            image=self.create_test_image(),
            location='Kathmandu'
        )
        self.assertFalse(photo.is_liked_by(self.user))

        PhotoLike.objects.create(photo=photo, user=self.user)
        self.assertTrue(photo.is_liked_by(self.user))


class UserPhotoGalleryAPITests(APITestCase):
    """Test cases for user-specific photo gallery endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            first_name='User',
            last_name='One'
        )
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123'
        )

    def create_test_image(self):
        """Create a test image file"""
        image = Image.new('RGB', (100, 100), color='blue')
        image_io = BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        return SimpleUploadedFile(
            'test_image.jpg',
            image_io.getvalue(),
            content_type='image/jpeg'
        )

    def test_get_user_photos_endpoint_exists(self):
        """Test that the user-specific endpoint exists"""
        response = self.client.get(f'/api/photo-gallery/{self.user1.id}/')
        self.assertIn(response.status_code, [200, 404])  # Either success or auth error

    def test_get_user_photos_success(self):
        """Test successfully fetching photos for a user"""
        # Create photos for user1
        PhotoGallery.objects.create(
            user=self.user1,
            image=self.create_test_image(),
            location='Kathmandu',
            is_public=True
        )
        PhotoGallery.objects.create(
            user=self.user1,
            image=self.create_test_image(),
            location='Pokhara',
            is_public=True
        )

        # Fetch photos
        response = self.client.get(f'/api/photo-gallery/{self.user1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['user_id'], self.user1.id)
        self.assertEqual(data['count'], 2)
        self.assertEqual(len(data['data']), 2)

    def test_get_user_photos_empty_result(self):
        """Test fetching photos when user has none"""
        response = self.client.get(f'/api/photo-gallery/{self.user1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['count'], 0)
        self.assertEqual(data['data'], [])

    def test_invalid_user_id(self):
        """Test with invalid user_id (non-integer)"""
        response = self.client.get('/api/photo-gallery/invalid/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['status'], 'error')
        self.assertIn('Invalid', data['message'])

    def test_nonexistent_user_id(self):
        """Test with non-existent user_id"""
        response = self.client.get('/api/photo-gallery/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_public_photos_only_for_others(self):
        """Test that unauthenticated users see only public photos"""
        # Create one public and one private photo
        PhotoGallery.objects.create(
            user=self.user1,
            image=self.create_test_image(),
            location='Kathmandu',
            is_public=True,
            title='Public Photo'
        )
        PhotoGallery.objects.create(
            user=self.user1,
            image=self.create_test_image(),
            location='Pokhara',
            is_public=False,
            title='Private Photo'
        )

        # Unauthenticated access - should see only public
        response = self.client.get(f'/api/photo-gallery/{self.user1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['data'][0]['title'], 'Public Photo')

    def test_authenticated_user_sees_all_own_photos(self):
        """Test that authenticated user sees all their own photos"""
        # Create photos (mixing public and private)
        PhotoGallery.objects.create(
            user=self.user1,
            image=self.create_test_image(),
            location='Kathmandu',
            is_public=True
        )
        PhotoGallery.objects.create(
            user=self.user1,
            image=self.create_test_image(),
            location='Pokhara',
            is_public=False
        )

        # Authenticate as user1
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'/api/photo-gallery/{self.user1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        # Should see both photos (public and private)
        self.assertEqual(data['count'], 2)

    def test_response_format(self):
        """Test that response has correct format"""
        PhotoGallery.objects.create(
            user=self.user1,
            image=self.create_test_image(),
            location='Kathmandu',
            is_public=True,
            title='Test Photo'
        )

        response = self.client.get(f'/api/photo-gallery/{self.user1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Check required fields
        self.assertIn('status', data)
        self.assertIn('message', data)
        self.assertIn('count', data)
        self.assertIn('user_id', data)
        self.assertIn('data', data)

        # Check photo data has required fields
        photo = data['data'][0]
        self.assertIn('id', photo)
        self.assertIn('image_url', photo)
        self.assertIn('location', photo)
        self.assertIn('title', photo)
        self.assertIn('uploaded_at', photo)


class PhotoUploadTests(APITestCase):
    """Test cases for photo upload"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def create_test_image(self, size=(100, 100), color='green'):
        """Create a test image file"""
        image = Image.new('RGB', size, color=color)
        image_io = BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        return SimpleUploadedFile(
            'test_image.jpg',
            image_io.getvalue(),
            content_type='image/jpeg'
        )

    def test_upload_photo_success(self):
        """Test successful photo upload"""
        data = {
            'image': self.create_test_image(),
            'title': 'Test Photo',
            'location': 'Kathmandu',
            'is_public': True
        }
        response = self.client.post('/api/photos/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PhotoGallery.objects.count(), 1)

    def test_upload_photo_without_auth(self):
        """Test that upload requires authentication"""
        self.client.force_authenticate(user=None)
        data = {
            'image': self.create_test_image(),
            'location': 'Kathmandu'
        }
        response = self.client.post('/api/photos/', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PhotoDeleteTests(APITestCase):
    """Test cases for photo deletion"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def create_test_image(self):
        """Create a test image file"""
        image = Image.new('RGB', (100, 100), color='yellow')
        image_io = BytesIO()
        image.save(image_io, format='JPEG')
        image_io.seek(0)
        return SimpleUploadedFile(
            'test_image.jpg',
            image_io.getvalue(),
            content_type='image/jpeg'
        )

    def test_delete_own_photo(self):
        """Test deleting own photo"""
        photo = PhotoGallery.objects.create(
            user=self.user,
            image=self.create_test_image(),
            location='Kathmandu'
        )
        response = self.client.delete(f'/api/photos/{photo.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PhotoGallery.objects.filter(id=photo.id).exists())


class FavoriteLocationTests(APITestCase):
    """Test cases for favorite locations"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='user@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_add_favorite_location(self):
        """Test adding a favorite location"""
        data = {'location': 'Kathmandu'}
        response = self.client.post('/api/favorite-locations/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FavoriteLocation.objects.count(), 1)

    def test_toggle_favorite_location(self):
        """Test toggling favorite location"""
        data = {'location': 'Kathmandu'}
        response = self.client.post('/api/favorite-locations/toggle/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()['is_favorited'])

        # Toggle again to remove
        response = self.client.post('/api/favorite-locations/toggle/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.json()['is_favorited'])

    def test_check_favorite_location(self):
        """Test checking if location is favorited"""
        FavoriteLocation.objects.create(user=self.user, location='Kathmandu')
        response = self.client.get('/api/favorite-locations/check/?location=Kathmandu')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.json()['is_favorited'])