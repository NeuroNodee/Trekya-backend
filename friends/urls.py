"""friends/urls.py"""

from django.urls import path

from . import views

urlpatterns = [
    # ── Send ──────────────────────────────────────────────────────────────────
    path(
        "friend-request/send/<int:receiver_id>/",
        views.send_friend_request,
        name="send_friend_request",
    ),
    # ── Accept / Decline / Withdraw ───────────────────────────────────────────
    path(
        "friend-request/<int:request_id>/accept/",
        views.accept_friend_request,
        name="accept_friend_request",
    ),
    path(
        "friend-request/<int:request_id>/decline/",
        views.decline_friend_request,
        name="decline_friend_request",
    ),
    path(
        "friend-request/<int:request_id>/withdraw/",
        views.withdraw_friend_request,
        name="withdraw_friend_request",
    ),
    # ── Lists ─────────────────────────────────────────────────────────────────
    path(
        "friend-requests/received/",
        views.pending_received_requests,
        name="pending_received_requests",
    ),
    path(
        "friend-requests/sent/",
        views.sent_requests,          # supports ?receiver_id= for targeted polling
        name="sent_requests",
    ),
    # ── Friends ───────────────────────────────────────────────────────────────
    path(
        "friends/",
        views.list_friends,
        name="list_friends",
    ),
    path(
        "friends/remove/<int:user_id>/",
        views.remove_friend,
        name="remove_friend",
    ),
]