from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Notification(models.Model):
    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="notifications",
        through='NotificationUser'  # use custom through model
    )
    status = models.CharField(max_length=20, choices=[
        ('Warning', 'Warning'),
        ('Info', 'Info'),
        ('Success', 'Success'),
        ('Error', 'Error'),
    ])
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    latest = models.BooleanField(default=True)

    def __str__(self):
        return f"Notification - {self.status}"

    @classmethod
    def update_latest_flags(cls):
        cutoff = timezone.now() - timedelta(hours=24)
        cls.objects.filter(created_at__lt=cutoff, latest=True).update(latest=False)


class NotificationUser(models.Model):
    """Tracks per-user state for each notification"""
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_dismissed = models.BooleanField(default=False)  # user closed it
    dismissed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('notification', 'user')

    def dismiss(self):
        self.is_dismissed = True
        self.dismissed_at = timezone.now()
        self.save()


class User_activity_notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=255, choices=[
        ('location', 'Location'),
        ('kit', 'Kit'),
        ('post', 'Post'),
        ('like', 'Like'),
        ('comment', 'Comment'),
    ])
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.user.email + "-" + self.action
    
    
    