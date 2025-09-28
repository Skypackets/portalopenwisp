from django.contrib import admin

from .models import Page
from .utils import publish_page_assets


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "brand", "site", "name", "status", "rev", "updated_at")
    list_filter = ("tenant", "status")
    search_fields = ("name",)

    actions = ("publish_selected",)

    def publish_selected(self, request, queryset):
        for page in queryset:
            result = publish_page_assets(
                page.tenant_id, "admin", page.html or "", page.css or "", page.js or ""
            )
            page.status = "published"
            page.rev = result.html_path.rsplit("/", 1)[-1]
            page.save(update_fields=["status", "rev"])
        self.message_user(request, f"Published {queryset.count()} page(s)")

    publish_selected.short_description = "Publish selected pages"
