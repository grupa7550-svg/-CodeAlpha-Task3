from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import Event, Registration

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class EventSerializer(serializers.ModelSerializer):
    organizer = serializers.ReadOnlyField(source="organizer.username")
    seats_left = serializers.IntegerField(read_only=True)

    class Meta:
        model = Event
        fields = [
            "id", "title", "description", "location", "start_time",
            "end_time", "capacity", "seats_left", "organizer", "created_at",
        ]

    def validate(self, attrs):
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if start and end and end <= start:
            raise serializers.ValidationError("end_time must be after start_time.")
        return attrs


class RegistrationSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.username")
    event_title = serializers.ReadOnlyField(source="event.title")

    class Meta:
        model = Registration
        fields = [
            "id", "user", "event", "event_title", "full_name", "email",
            "phone", "status", "registered_at", "cancelled_at",
        ]
        read_only_fields = ["status", "registered_at", "cancelled_at"]

    def validate_event(self, event):
        if not event.is_upcoming:
            raise serializers.ValidationError("This event has already started.")
        return event

    def validate(self, attrs):
        user = self.context["request"].user
        event = attrs["event"]
        if Registration.objects.filter(
            user=user, event=event, status=Registration.Status.CONFIRMED
        ).exists():
            raise serializers.ValidationError("You are already registered for this event.")
        return attrs

    def create(self, validated_data):
        # Lock the event row so two people can't take the last seat at once
        with transaction.atomic():
            event = Event.objects.select_for_update().get(pk=validated_data["event"].pk)
            if event.seats_left <= 0:
                raise serializers.ValidationError({"event": "This event is full."})
            return Registration.objects.create(**validated_data)
