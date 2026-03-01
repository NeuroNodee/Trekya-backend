import functools
import logging

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .models import DEFAULT_FRIEND_REQUEST_MESSAGE, FriendRequest, Friendship

logger = logging.getLogger(__name__)
User = get_user_model()


# ─── response helpers ─────────────────────────────────────────────────────────

def json_ok(data: dict, status: int = 200) -> JsonResponse:
    return JsonResponse({"success": True, **data}, status=status)


def json_err(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"success": False, "error": message}, status=status)


# ─── flexible auth decorator ──────────────────────────────────────────────────

def flexible_login_required(view_func):
    """
    Works with Django session auth **and** JWT Bearer tokens.

    Priority:
      1. request.user is already authenticated (session / middleware)
      2. Authorization: Bearer <token> header  (JWT via simplejwt)

    If neither is present / valid → 401.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        print("=== flexible_login_required HIT ===")
        print("PATH:", request.path)
        print("AUTH:", request.headers.get("Authorization", "NONE"))
        print("USER:", request.user)
        print("IS AUTH:", request.user.is_authenticated)
        # 1 – session auth
        if request.user.is_authenticated:
            return view_func(request, *args, **kwargs)

        # 2 – JWT Bearer
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token_str = auth_header.split(" ", 1)[1]
            try:
                from rest_framework_simplejwt.tokens import AccessToken  # type: ignore
                token = AccessToken(token_str)
                print("user_id from token:", token["user_id"], type(token["user_id"]))

                user = User.objects.get(pk=int(token["user_id"]), is_active=True)
                print("found user:", user)
                request.user = user
                
            except Exception as exc:  # noqa: BLE001
                print("JWT EXCEPTION:", type(exc).__name__, exc)
                logger.debug("JWT auth failed: %s", exc)
                return json_err("Invalid or expired token.", 401)
            return view_func(request, *args, **kwargs)

        return json_err("Authentication required.", 401)

    return wrapper


# ─── send ─────────────────────────────────────────────────────────────────────

@csrf_exempt
@flexible_login_required
@require_POST
def send_friend_request(request, receiver_id: int):
    """
    POST /friend-request/send/<receiver_id>/
    Body (form-data or JSON):  message  (optional, max 200 chars)

    Returns 201 on success.
    Returns 409 if a pending/accepted relationship already exists.
    """
    if request.user.pk == int(receiver_id):
        return json_err("You cannot send a friend request to yourself.")

    receiver = get_object_or_404(User, pk=receiver_id, is_active=True)

    # already friends?
    if Friendship.are_friends(request.user, receiver):
        return json_err("You are already friends with this user.", 409)

    # any pending request in either direction?
    existing = FriendRequest.objects.filter(
        Q(sender=request.user, receiver=receiver) |
        Q(sender=receiver, receiver=request.user),
        status=FriendRequest.Status.PENDING,
    ).first()

    if existing:
        if existing.sender == request.user:
            return json_err("You already have a pending request to this user.", 409)
        return json_err("This user already sent you a friend request. Check your notifications.", 409)

    # parse message from form-data or JSON body
    message = _get_message(request)
    if len(message) > 200:
        return json_err("Message must be 200 characters or fewer.")

    try:
        resend_case = FriendRequest.objects.filter(
            Q(sender=request.user, receiver=receiver),
            status=FriendRequest.Status.WITHDRAWN,
        ).first()
        if resend_case:
            resend_case.delete()
        resend_case = FriendRequest.objects.filter(
            Q(sender=request.user, receiver=receiver),
            status=FriendRequest.Status.DECLINED,
        ).first()
        if resend_case:
            resend_case.delete()
        fr = FriendRequest.objects.create(
            sender=request.user,
            receiver=receiver,
            message=message,
        )
    except IntegrityError:
        return json_err("A friend request to this user already exists.", 409)

    logger.info("Friend request %s: %s → %s", fr.pk, request.user.pk, receiver_id)
    return json_ok(
        {"message": "Friend request sent.", "request_id": fr.pk},
        status=201,
    )


# ─── accept ───────────────────────────────────────────────────────────────────

@csrf_exempt
@flexible_login_required
@require_POST
def accept_friend_request(request, request_id: int):
    """POST /friend-request/<request_id>/accept/"""
    fr = get_object_or_404(
        FriendRequest,
        pk=request_id,
        receiver=request.user,
        status=FriendRequest.Status.PENDING,
    )
    try:
        fr.accept()
    except ValueError as exc:
        return json_err(str(exc))

    logger.info("Friend request %s accepted by %s", fr.pk, request.user.pk)
    return json_ok({"message": "Friend request accepted."})


# ─── decline ──────────────────────────────────────────────────────────────────

@csrf_exempt
@flexible_login_required
@require_POST
def decline_friend_request(request, request_id: int):
    """POST /friend-request/<request_id>/decline/"""
    fr = get_object_or_404(
        FriendRequest,
        pk=request_id,
        receiver=request.user,
        status=FriendRequest.Status.PENDING,
    )
    try:
        fr.decline()
    except ValueError as exc:
        return json_err(str(exc))

    logger.info("Friend request %s declined by %s", fr.pk, request.user.pk)
    return json_ok({"message": "Friend request declined."})


# ─── withdraw (sender cancels) ────────────────────────────────────────────────
@csrf_exempt
@flexible_login_required
@require_POST
def withdraw_friend_request(request, request_id: int):
    """POST /friend-request/<request_id>/withdraw/"""
    fr = get_object_or_404(
        FriendRequest,
        pk=request_id,
        sender=request.user,
        status=FriendRequest.Status.PENDING,
    )
    try:
        fr.withdraw()
    except ValueError as exc:
        return json_err(str(exc))

    logger.info("Friend request %s withdrawn by %s", fr.pk, request.user.pk)
    return json_ok({"message": "Friend request withdrawn."})


# ─── pending received (notifications) ────────────────────────────────────────
@csrf_exempt
@flexible_login_required
def pending_received_requests(request):
    """
    GET /friend-requests/received/
    Used by notification panels to show incoming friend requests.
    """
    print("USER:", request.user)
    print("AUTH HEADER:", request.headers.get("Authorization", "NONE"))
    requests_qs = (
        FriendRequest.objects
        .filter(receiver=request.user, status=FriendRequest.Status.PENDING)
        .select_related("sender")
        .order_by("-created_at")
    )

    data = [
        {
            "request_id":       fr.pk,
            "sender_id":        fr.sender.pk,
            "sender_username":  fr.sender.email,
            "sender_full_name": fr.sender.get_full_name(),
            "message":          fr.message,
            "sent_at":          fr.created_at.isoformat(),
        }
        for fr in requests_qs
    ]
    return json_ok({"pending_requests": data, "count": len(data)})


# ─── sent requests (sender polls this) ───────────────────────────────────────
@csrf_exempt
@flexible_login_required
def sent_requests(request):
    """
    GET /friend-requests/sent/
    The frontend polls this while a request is pending to detect
    accept / decline by the other user.

    Optional query param:  ?receiver_id=<id>  – filter to one user.
    """
    qs = (
        FriendRequest.objects
        .filter(sender=request.user)
        .exclude(status=FriendRequest.Status.WITHDRAWN)
        .select_related("receiver")
        .order_by("-created_at")
    )

    # allow filtering by receiver so the poll can be lightweight
    receiver_id = request.GET.get("receiver_id")
    if receiver_id:
        qs = qs.filter(receiver_id=receiver_id)

    data = [
        {
            "request_id":          fr.pk,
            "receiver_id":         fr.receiver.pk,
            "receiver_username":   fr.receiver.email,
            "receiver_full_name":  fr.receiver.get_full_name(),
            "message":             fr.message,
            "status":              fr.status,
            "sent_at":             fr.created_at.isoformat(),
            "updated_at":          fr.updated_at.isoformat(),
        }
        for fr in qs
    ]
    return json_ok({"sent_requests": data})


# ─── friends list ─────────────────────────────────────────────────────────────
@csrf_exempt
@flexible_login_required
def list_friends(request):
    """GET /friends/"""
    friends = Friendship.get_friends(request.user)
    data = [
        {
            "id":        f.pk,
            "email":     f.email,
            "full_name": f.get_full_name(),
        }
        for f in friends
    ]
    return json_ok({"friends": data, "count": len(data)})


# ─── remove friend ────────────────────────────────────────────────────────────

@csrf_exempt
@flexible_login_required
@require_POST
def remove_friend(request, user_id: int):
    """POST /friends/remove/<user_id>/"""
    other = get_object_or_404(User, pk=user_id, is_active=True)
    u1, u2 = sorted([request.user, other], key=lambda u: u.pk)
    deleted, _ = Friendship.objects.filter(user1=u1, user2=u2).delete()
    if not deleted:
        return json_err("You are not friends with this user.", 404)
    logger.info("Friendship removed: %s ↔ %s", request.user.pk, user_id)
    return json_ok({"message": "Friend removed."})


# ─── internal helper ──────────────────────────────────────────────────────────

def _get_message(request) -> str:
    """Extract message from form-data or JSON body."""
    # form-data (default for the React component using FormData)
    msg = (request.POST.get("message") or "").strip()
    if msg:
        return msg

    # JSON body fallback
    if request.content_type and "json" in request.content_type:
        import json
        try:
            body = json.loads(request.body)
            msg = (body.get("message") or "").strip()
        except (ValueError, AttributeError):
            pass

    return msg or DEFAULT_FRIEND_REQUEST_MESSAGE