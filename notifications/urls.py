from django.urls import path
from . import views

urlpatterns = [
    path('fetch-notifications/', views.fetch_notifications, name='fetch-notifications'),
    path('dismiss-notification/<int:notification_id>/', views.dismiss_notification, name='dismiss-notification'),
    path('trigger-notification/', views.trigger_notification, name='trigger-notification'),
    path('fetch-user-activity-notifications/', views.fetch_user_activity_notifications, name='fetch-user-activity-notifications'),
    path('remove-user-activity-notification/<int:notification_id>/', views.remove_user_activity_notification, name='remove-user-activity-notification'),
]