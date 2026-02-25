from django.urls import path
from . import views

urlpatterns = [
    path('fetch-notifications/', views.fetch_notifications, name='fetch-notifications'),
    path('dismiss-notification/<int:notification_id>/', views.dismiss_notification, name='dismiss-notification'),
]