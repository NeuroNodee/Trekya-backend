from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

User = get_user_model()

class PhotoGallery(models.Model):
    """
    Model to store user-uploaded photos with location information.
    Each photo is linked to a user and associated with a specific location.
    """

    LOCATION_CHOICES = (
        ('Illam', 'Illam'),
        ('Dharan', 'Dharan'),
        ('Koshi Tappu', 'Koshi Tappu'),
        ('Mt Everest Base Camp', 'Mt Everest Base Camp'),
        ('Makalu Trek (Everest Region)', 'Makalu Trek (Everest Region)'),
        ('Mt Everest (Summit attempt)', 'Mt Everest (Summit attempt)'),
        ('Janaki Temple', 'Janaki Temple'),
        ('Gaurishankar Region Trek', 'Gaurishankar Region Trek'),
        ('Kathmandu', 'Kathmandu'),
        ('Bhaktapur', 'Bhaktapur'),
        ('Lalitpur', 'Lalitpur'),
        ('Langtang Valley (Trek)', 'Langtang Valley (Trek)'),
        ('Gosaikunda Lake', 'Gosaikunda Lake'),
        ('Machapuchare (Fishtail)', 'Machapuchare (Fishtail)'),
        ('Ghandruk Village', 'Ghandruk Village'),
        ('Pokhara', 'Pokhara'),
        ('Phewa Lake', 'Phewa Lake'),
        ('Ghorepani–Poon Hill', 'Ghorepani–Poon Hill'),
        ('Annapurna Circuit', 'Annapurna Circuit'),
        ('Annapurna Base Camp (ABC) Trek', 'Annapurna Base Camp (ABC) Trek'),
        ('Dhaulagiri Circuit Trek', 'Dhaulagiri Circuit Trek'),
        ('Lumbini', 'Lumbini'),
        ('Bardia National Park', 'Bardia National Park'),
        ('Langtang National Park', 'Langtang National Park'),
        ('Sagarmatha National Park', 'Sagarmatha National Park'),
        ('Rara Lake', 'Rara Lake'),
        ('Rara National Park', 'Rara National Park'),
        ('Shey Phoksundo Lake', 'Shey Phoksundo Lake'),
        ('Shey Phoksundo National Park', 'Shey Phoksundo National Park'),
        ('Api Mountain', 'Api Mountain'),
        ('Khaptad National Park', 'Khaptad National Park'),
        ('Mustang', 'Mustang'),
        ('Manang', 'Manang'),
        ('Other', 'Other'),
    )


    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')

    image = models.ImageField(
        upload_to='travelkit_items/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])]
    )

    location = models.CharField(max_length=50, choices=LOCATION_CHOICES, default='Other')
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_public = models.BooleanField(default=True, help_text="If True, photo is visible to all users. If False, only you can see it.")

    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Photo Gallery'
        verbose_name_plural = 'Photo Galleries'

    def __str__(self):
        return f"{self.user.email}'s photo - {self.location}"

    @property
    def get_image_url(self):
        if self.image:
            return self.image.url
        return None

    @property
    def likes_count(self):
        """Count total likes for this photo"""
        return self.likes.count()

    def is_liked_by(self, user):
        """Check if a specific user has liked this photo"""
        if not user or not user.is_authenticated:
            return False
        return self.likes.filter(user=user).exists()


class PhotoLike(models.Model):
    """
    Model to store likes/upvotes on photos.
    Each user can like a photo only once.
    """
    photo = models.ForeignKey(PhotoGallery, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photo_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('photo', 'user')
        ordering = ['-created_at']
        verbose_name = 'Photo Like'
        verbose_name_plural = 'Photo Likes'

    def __str__(self):
        return f"{self.user.username} liked {self.photo.id}"

class FavoriteLocation(models.Model):
    """
    Model to track user's favorite travel destinations (locations).
    """
    LOCATION_CHOICES = (
        ('Kathmandu', 'Kathmandu'),
        ('Pokhara', 'Pokhara'),
        ('Janaki', 'Janaki'),
        ('Lumbini', 'Lumbini'),
        ('Bhaktapur', 'Bhaktapur'),
        ('Dhaulagiri', 'Dhaulagiri'),
        ('Gaurishankar', 'Gaurishankar'),
        ('Annapurna', 'Annapurna'),
        ('EverestRegion', 'Everest Region'),
        ('LangtangNationalPark', 'Langtang National Park'),
        ('Ghorepani', 'Ghorepani'),
        ('Ghandruk', 'Ghandruk'),
        ('GosaikundaLake', 'Gosaikunda Lake'),
        ('Machhapuchhre', 'Machhapuchhre'),
        ('Khaptad', 'Khaptad'),
        ('KoshiTappu', 'Koshi Tappu'),
        ('Rara', 'Rara'),
        ('Shey', 'Shey'),
        ('SheyLake', 'Shey Lake'),
        ('Bardia', 'Bardia'),
        ('Dharan', 'Dharan'),
        ('Illam', 'Illam'),
        ('Lalitpur', 'Lalitpur'),
        ('Api', 'Api'),
        ('Other', 'Other'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_locations')
    location = models.CharField(max_length=50, choices=LOCATION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'location')
        ordering = ['-created_at']
        verbose_name = 'Favorite Location'
        verbose_name_plural = 'Favorite Locations'

    def __str__(self):
        return f"{self.user.email} - {self.location}"