from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from . import views

urlpatterns = [
    # Auth
    path("auth/signup/", views.SignupView.as_view(), name="signup"),
    path("auth/login/", obtain_auth_token, name="login"),
    # Events
    path("events/", views.EventListCreateView.as_view(), name="event-list"),
    path("events/<int:pk>/", views.EventDetailView.as_view(), name="event-detail"),
    path(
        "events/<int:pk>/registrations/",
        views.EventRegistrationsView.as_view(),
        name="event-registrations",
    ),
    # Registrations
    path("registrations/", views.RegistrationCreateView.as_view(), name="register"),
    path("registrations/mine/", views.MyRegistrationsView.as_view(), name="my-registrations"),
    path("registrations/<int:pk>/", views.RegistrationDetailView.as_view(), name="registration-detail"),
    path("registrations/<int:pk>/cancel/", views.RegistrationCancelView.as_view(), name="registration-cancel"),
]
