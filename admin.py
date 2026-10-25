from django.contrib import admin

from .models import Event, Registration


class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 0
    readonly_fields = ["registered_at", "cancelled_at"]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "location", "start_time", "capacity", "seats_left", "organizer"]
    list_filter = ["start_time", "organizer"]
    search_fields = ["title", "location"]
    inlines = [RegistrationInline]


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ["user", "event", "full_name", "email", "status", "registered_at"]
    list_filter = ["status", "event"]
    search_fields = ["full_name", "email", "user__username"]
