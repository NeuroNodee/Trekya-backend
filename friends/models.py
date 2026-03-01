"""
friends/models.py  –  Production-ready FriendRequest + Friendship models

Key design decisions
─────────────────────
• unique_together on (sender, receiver) prevents duplicate rows at the DB level.
• Friendship is always stored with user1.pk < user2.pk so the pair is canonical
  and we can never accidentally create (A, B) and (B, A) both.
• Status transitions are enforced in Python (accept/decline/withdraw) so they
  can raise descriptive ValueError instead of silent bad state.
• All timestamps are UTC-aware (auto_now / auto_now_add).
"""

from django.contrib.auth import get_user_model
from django.db import models, transaction

User = get_user_model()

DEFAULT_FRIEND_REQUEST_MESSAGE = "Hi! I'd like to connect with you on this platform."


class FriendRequest(models.Model):

    class Status(models.TextChoices):
        PENDING   = "pending",   "Pending"
        ACCEPTED  = "accepted",  "Accepted"
        DECLINED  = "declined",  "Declined"
        WITHDRAWN = "withdrawn", "Withdrawn"

    sender   = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_friend_requests",
        db_index=True,
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_friend_requests",
        db_index=True,
    )
    message = models.TextField(
        max_length=500,
        default=DEFAULT_FRIEND_REQUEST_MESSAGE,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together      = ("sender", "receiver")
        ordering             = ["-created_at"]
        verbose_name         = "Friend Request"
        verbose_name_plural  = "Friend Requests"
        indexes = [
            # composite index used by the "any pending between these two users" query
            models.Index(fields=["sender", "receiver", "status"], name="fr_sender_receiver_status_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.sender_id} → {self.receiver_id} [{self.status}]"

    # ── transitions ───────────────────────────────────────────────────────────

    @transaction.atomic
    def accept(self) -> None:
        if self.status != self.Status.PENDING:
            raise ValueError("Only pending requests can be accepted.")
        self.status = self.Status.ACCEPTED
        self.save(update_fields=["status", "updated_at"])
        # create canonical friendship
        u1, u2 = sorted([self.sender, self.receiver], key=lambda u: u.pk)
        Friendship.objects.get_or_create(user1=u1, user2=u2)

    def decline(self) -> None:
        if self.status != self.Status.PENDING:
            raise ValueError("Only pending requests can be declined.")
        self.status = self.Status.DECLINED
        self.save(update_fields=["status", "updated_at"])

    def withdraw(self) -> None:
        if self.status != self.Status.PENDING:
            raise ValueError("Only pending requests can be withdrawn.")
        self.status = self.Status.WITHDRAWN
        self.save(update_fields=["status", "updated_at"])


class Friendship(models.Model):
    """
    Canonical friendship record.
    user1.pk is always < user2.pk – enforced in FriendRequest.accept()
    and in the remove_friend view.
    """
    user1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="friendships_as_user1",
    )
    user2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="friendships_as_user2",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together     = ("user1", "user2")
        ordering            = ["-created_at"]
        verbose_name        = "Friendship"
        verbose_name_plural = "Friendships"

    def __str__(self) -> str:
        return f"{self.user1_id} ↔ {self.user2_id}"

    # ── class methods ─────────────────────────────────────────────────────────

    @classmethod
    def are_friends(cls, user_a: User, user_b: User) -> bool:
        u1, u2 = sorted([user_a, user_b], key=lambda u: u.pk)
        return cls.objects.filter(user1=u1, user2=u2).exists()

    @classmethod
    def get_friends(cls, user: User) -> list:
        from django.db.models import Q
        friendships = (
            cls.objects
            .filter(Q(user1=user) | Q(user2=user))
            .select_related("user1", "user2")
        )
        return [f.user2 if f.user1 == user else f.user1 for f in friendships]