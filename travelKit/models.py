from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

"""the Location, TravelKitItem and Travel kit information are to be set by admin like a predefined information"""


class Location(models.Model):
    """
    Location model to store location information
    """
    name = models.CharField(max_length=100, db_index=True, unique=True)
    country = models.CharField(max_length=100, blank=True, default="Nepal")

    def __str__(self):
        return self.name


class TravelKitItem(models.Model):
    """
    TravelKitItem model to store travel kit item information
    """
    CATEGORY_CHOICES = [
        ("clothing", "Clothing"),
        ("gear", "Gear"),
        ("medical", "Medical"),
        ("electronics", "Electronics"),
    ]
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES) 
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='travelkit_items/', blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2,default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class TravelKit(models.Model):
    """
    TravelKit model to store travel kit information: it maps item and location to show recommendations
    """
    name = models.CharField(max_length=150, db_index=True)
    description = models.TextField()
    

    locations = models.ManyToManyField(
        Location,
        related_name="travel_kits"
    )

    items = models.ManyToManyField(
        TravelKitItem,
        related_name="kits"
    )

    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class UserPersonalizedTravelKit(models.Model):
    """
    UserPersonalizedTravelKit model to store user's personalized travel kit information: user would select from recommended and extra items.
    """
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'location'],
                name='unique_user_location_travelkit'
            )
        ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="personal_travel_kits")
    location = models.ForeignKey("Location", on_delete=models.SET_NULL, null=True, blank=True)
    
    selected_items = models.JSONField(default=list, blank=True)

    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.location.name if self.location else 'No Location'}"


class FavoriteTravelKit(models.Model):
    """
    Model to track user's favorite TravelKit items and kits.
    Users can favorite individual items or complete travel kits for their wishlist.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_travel_kits')
    travel_kit = models.ForeignKey(TravelKit, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'travel_kit')
        ordering = ['-created_at']
        verbose_name = 'Favorite Travel Kit'
        verbose_name_plural = 'Favorite Travel Kits'

    def __str__(self):
        return f"{self.user.email} - {self.travel_kit.name}"


class FavoriteTravelKitItem(models.Model):
    """
    Model to track user's favorite TravelKit items for wishlist/shopping purposes.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_items')
    item = models.ForeignKey(TravelKitItem, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'item')
        ordering = ['-created_at']
        verbose_name = 'Favorite Travel Kit Item'
        verbose_name_plural = 'Favorite Travel Kit Items'

    def __str__(self):
        return f"{self.user.email} - {self.item.name}"
