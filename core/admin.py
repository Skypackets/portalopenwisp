from django.contrib import admin

from .models import SSID, Brand, Controller, Site, Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "status", "plan", "created_at")
    search_fields = ("name",)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "name", "created_at")
    list_filter = ("tenant",)
    search_fields = ("name",)


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "brand", "name", "timezone", "created_at")
    list_filter = ("tenant", "brand")
    search_fields = ("name",)


@admin.register(SSID)
class SSIDAdmin(admin.ModelAdmin):
    list_display = ("id", "site", "name", "auth_mode", "controller", "created_at")
    list_filter = ("auth_mode",)
    search_fields = ("name",)


@admin.register(Controller)
class ControllerAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "type", "base_url", "created_at")
    list_filter = ("type",)
