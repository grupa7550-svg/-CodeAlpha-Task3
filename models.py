from django.conf import settings
from django.db import models
from django.utils import timezone


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=50)
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return self.title

    @property
    def active_registrations(self):
        return self.registrations.filter(status=Registration.Status.CONFIRMED)

    @property
    def seats_left(self):
        return max(self.capacity - self.active_registrations.count(), 0)

    @property
    def is_upcoming(self):
        return self.start_time > timezone.now()


class Registration(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="registrations"
    )
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.CONFIRMED
    )
    registered_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-registered_at"]
        constraints = [
            # A user can have only one confirmed registration per event
            models.UniqueConstraint(
                fields=["user", "event"],
                condition=models.Q(status="confirmed"),
                name="unique_active_registration_per_user_event",
            )
        ]

    def __str__(self):
        return f"{self.user} -> {self.event} ({self.status})"

    def cancel(self):
        self.status = self.Status.CANCELLED
        self.cancelled_at = timezone.now()
        self.save(update_fields=["status", "cancelled_at"])
