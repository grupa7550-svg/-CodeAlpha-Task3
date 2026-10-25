from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Event, Registration

User = get_user_model()


class EventRegistrationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.organizer = User.objects.create_user("org", password="pass1234")
        self.alice = User.objects.create_user("alice", password="pass1234")
        self.bob = User.objects.create_user("bob", password="pass1234")
        self.event = Event.objects.create(
            title="PyCon", location="Chennai", capacity=1,
            start_time=timezone.now() + timedelta(days=5),
            end_time=timezone.now() + timedelta(days=6),
            organizer=self.organizer,
        )

    def register(self, user, event=None):
        self.client.force_authenticate(user)
        return self.client.post("/api/registrations/", {
            "event": (event or self.event).id,
            "full_name": user.username.title(),
            "email": f"{user.username}@example.com",
        })

    def test_public_can_view_events(self):
        r = self.client.get("/api/events/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["count"], 1)
        r = self.client.get(f"/api/events/{self.event.id}/")
        self.assertEqual(r.data["seats_left"], 1)

    def test_anonymous_cannot_register(self):
        r = self.client.post("/api/registrations/", {"event": self.event.id})
        self.assertEqual(r.status_code, 401)

    def test_register_and_duplicate(self):
        self.assertEqual(self.register(self.alice).status_code, 201)
        self.assertEqual(self.register(self.alice).status_code, 400)

    def test_capacity_enforced(self):
        self.assertEqual(self.register(self.alice).status_code, 201)
        self.assertEqual(self.register(self.bob).status_code, 400)

    def test_cancel_frees_seat_and_allows_reregister(self):
        reg_id = self.register(self.alice).data["id"]
        self.client.force_authenticate(self.alice)
        r = self.client.post(f"/api/registrations/{reg_id}/cancel/")
        self.assertEqual(r.data["status"], "cancelled")
        self.assertEqual(self.register(self.bob).status_code, 201)

    def test_cannot_cancel_others_registration(self):
        reg_id = self.register(self.alice).data["id"]
        self.client.force_authenticate(self.bob)
        r = self.client.post(f"/api/registrations/{reg_id}/cancel/")
        self.assertEqual(r.status_code, 404)

    def test_my_registrations_only_shows_own(self):
        self.register(self.alice)
        self.client.force_authenticate(self.bob)
        self.assertEqual(self.client.get("/api/registrations/mine/").data["count"], 0)

    def test_only_organizer_edits_event_and_sees_attendees(self):
        self.register(self.alice)
        self.client.force_authenticate(self.alice)
        self.assertEqual(self.client.patch(f"/api/events/{self.event.id}/", {"title": "X"}).status_code, 403)
        self.assertEqual(self.client.get(f"/api/events/{self.event.id}/registrations/").data["count"], 0)
        self.client.force_authenticate(self.organizer)
        self.assertEqual(self.client.patch(f"/api/events/{self.event.id}/", {"title": "X"}).status_code, 200)
        self.assertEqual(self.client.get(f"/api/events/{self.event.id}/registrations/").data["count"], 1)

    def test_signup_and_login_token(self):
        r = self.client.post("/api/auth/signup/", {"username": "new", "email": "n@x.com", "password": "secret123"})
        self.assertEqual(r.status_code, 201)
        r = self.client.post("/api/auth/login/", {"username": "new", "password": "secret123"})
        self.assertIn("token", r.data)
