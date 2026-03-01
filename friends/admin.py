# friends/admin.py

from django.contrib import admin
from .models import FriendRequest, Friendship


@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display  = ("id", "sender", "receiver", "status", "created_at", "updated_at")
    list_filter   = ("status",)
    search_fields = ("sender__username", "sender__email", "receiver__username", "receiver__email")
    ordering      = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display  = ("id", "user1", "user2", "created_at")
    search_fields = ("user1__username", "user1__email", "user2__username", "user2__email")
    ordering      = ("-created_at",)
    readonly_fields = ("created_at",)