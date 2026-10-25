from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Event, Registration
from .serializers import EventSerializer, RegistrationSerializer, SignupSerializer


class IsOrganizerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.organizer == request.user or request.user.is_staff


class SignupView(generics.CreateAPIView):
    """POST /api/auth/signup/  ->  create a user account."""
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]


class EventListCreateView(generics.ListCreateAPIView):
    """GET /api/events/  ->  list events (public).
    POST /api/events/ -> create an event (logged-in organizer)."""
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("upcoming") == "true":
            from django.utils import timezone
            qs = qs.filter(start_time__gt=timezone.now())
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(title__icontains=search)
        return qs

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)


class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET /api/events/<id>/ -> event details (public).
    PUT/PATCH/DELETE -> organizer only."""
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOrganizerOrReadOnly]


class RegistrationCreateView(generics.CreateAPIView):
    """POST /api/registrations/  ->  register the logged-in user for an event."""
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MyRegistrationsView(generics.ListAPIView):
    """GET /api/registrations/mine/  ->  the logged-in user's registrations."""
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Registration.objects.filter(user=self.request.user).select_related("event")


class RegistrationDetailView(generics.RetrieveAPIView):
    """GET /api/registrations/<id>/  ->  view one of your registrations."""
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Registration.objects.filter(user=self.request.user)


class RegistrationCancelView(APIView):
    """POST /api/registrations/<id>/cancel/  ->  cancel your registration."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            reg = Registration.objects.get(pk=pk, user=request.user)
        except Registration.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        if reg.status == Registration.Status.CANCELLED:
            return Response(
                {"detail": "Already cancelled."}, status=status.HTTP_400_BAD_REQUEST
            )
        reg.cancel()
        return Response(RegistrationSerializer(reg, context={"request": request}).data)


class EventRegistrationsView(generics.ListAPIView):
    """GET /api/events/<id>/registrations/  ->  attendee list (event organizer only)."""
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Registration.objects.filter(
            event_id=self.kwargs["pk"],
            event__organizer=user,
        ).select_related("user", "event")
