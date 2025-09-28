from django.contrib import admin

from .models import Campaign, Creative, Event, Slot


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "name", "status", "start_at", "end_at")
    list_filter = ("status",)
    search_fields = ("name",)


@admin.register(Creative)
class CreativeAdmin(admin.ModelAdmin):
    list_display = ("id", "campaign", "type", "width", "height")
    list_filter = ("type",)


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ("id", "page", "position", "sizes")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("id", "ts", "tenant", "site", "type")
    list_filter = ("type",)
