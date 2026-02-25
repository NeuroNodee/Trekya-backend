from django.db.models import Q
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Notification, NotificationUser
from django.utils import timezone


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_notifications(request):
    Notification.update_latest_flags()
    user = request.user

    notifications = Notification.objects.filter(
        Q(notificationuser__user=user, notificationuser__is_dismissed=False) |
        Q(users__isnull=True , notificationuser__is_dismissed=False)
    ).distinct().order_by('-created_at')

    data = list(notifications.values('id', 'message', 'status', 'created_at', 'latest'))
    return JsonResponse({'notifications': data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dismiss_notification(request, notification_id):
    user = request.user
    
    try:
        # Get the through model instance directly
        nu = NotificationUser.objects.get(
            notification_id=notification_id,
            user=user
        )
        nu.is_dismissed = True
        nu.dismissed_at = timezone.now()
        nu.save()
        
        # Optional: call the model's own dismiss method
        # nu.dismiss()   # if you prefer to keep logic in model
        
        return JsonResponse({'success': True})
        
    except NotificationUser.DoesNotExist:
        return JsonResponse(
            {'success': False, 'message': 'Notification not found or not targeted to you'},
            status=404
        )
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)