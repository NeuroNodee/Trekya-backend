from django.db.models import Q
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Notification, NotificationUser, User_activity_notification
from django.utils import timezone

from django.contrib.auth import get_user_model
User = get_user_model()

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_notification(request):
    try:
        print("=== TRIGGER NOTIFICATION ===")
        print("REQUEST DATA:", request.data)
        
        uploader_id = request.data.get('UploaderId')
        print("UPLOADER ID:", uploader_id)
        
        if uploader_id and uploader_id != request.user.id:
            uploader_user = User.objects.get(id=uploader_id)
            User_activity_notification.objects.create(
                user=uploader_user,
                action=request.data['action'],
                message=f"Your Post has been liked by " + request.user.first_name + " " + request.user.last_name
            )

        User_activity_notification.objects.create(
            user=request.user,
            action=request.data['action'],
            message=request.data['message']
        )

    except Exception as e:
        print("ERROR:", str(e))  # 👈 this will show the real error
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
    return JsonResponse({'success': True})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fetch_user_activity_notifications(request):
    user = request.user
    notifications = User_activity_notification.objects.filter(user=user).order_by('-created_at')
    data = list(notifications.values('id', 'message', 'action', 'created_at', 'is_read'))
    return JsonResponse({'notifications': data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_user_activity_notification(request, notification_id):
    user = request.user
    try:
        notification = User_activity_notification.objects.get(id=notification_id, user=user)
        notification.delete()
        return JsonResponse({'success': True})
    except User_activity_notification.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Notification not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

