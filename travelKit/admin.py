from django.contrib import admin
from .models import (
    Location,
    TravelKitItem,
    TravelKit,
    UserPersonalizedTravelKit,
    FavoriteTravelKit,
    FavoriteTravelKitItem
)

admin.site.register(Location)
admin.site.register(TravelKitItem)
admin.site.register(TravelKit)
admin.site.register(UserPersonalizedTravelKit)


@admin.register(FavoriteTravelKit)
class FavoriteTravelKitAdmin(admin.ModelAdmin):
    """Admin interface for FavoriteTravelKit model."""
    list_display = ('user', 'travel_kit', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('user__email', 'travel_kit__name')
    readonly_fields = ('created_at',)


@admin.register(FavoriteTravelKitItem)
class FavoriteTravelKitItemAdmin(admin.ModelAdmin):
    """Admin interface for FavoriteTravelKitItem model."""
    list_display = ('user', 'item', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('user__email', 'item__name')
    readonly_fields = ('created_at',)
