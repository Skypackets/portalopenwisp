from rest_framework import decorators, response, status, viewsets

from core.views import _get_request_tenant_id

from .models import Page, PageRevision
from .serializers import PageRevisionSerializer, PageSerializer
from .utils import publish_page_assets
from .builder import render_blocks


class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all().order_by("-updated_at")
    serializer_class = PageSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = _get_request_tenant_id(self.request)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        return qs

    @decorators.action(detail=True, methods=["post"], url_path="publish")
    def publish(self, request, pk=None):
        page = self.get_object()
        env = request.data.get("env", "dev")
        # Render from blocks if provided
        html = page.html or ""
        if page.blocks_json:
            html = render_blocks(page.blocks_json)
        result = publish_page_assets(page.tenant_id, env, html, page.css or "", page.js or "")
        page.status = "published"
        page.rev = result.html_path.rsplit("/", 1)[-1]
        page.save(update_fields=["status", "rev"])
        PageRevision.objects.create(
            page=page,
            rev=page.rev,
            html=html,
            css=page.css or "",
            js=page.js or "",
            blocks_json=page.blocks_json or [],
        )
        return response.Response(
            {
                "ok": True,
                "html_path": result.html_path,
                "css_path": result.css_path,
                "js_path": result.js_path,
            },
            status=status.HTTP_200_OK,
        )

    @decorators.action(detail=True, methods=["post"], url_path="save-blocks")
    def save_blocks(self, request, pk=None):
        page = self.get_object()
        blocks = request.data.get("blocks", [])
        page.blocks_json = blocks
        page.save(update_fields=["blocks_json"])
        return response.Response({"ok": True}, status=status.HTTP_200_OK)

    @decorators.action(detail=True, methods=["get"], url_path="preview")
    def preview(self, request, pk=None):
        page = self.get_object()
        html = render_blocks(page.blocks_json or [])
        sanitized = html  # builder renders sanitized parts already
        return response.Response({"html": sanitized}, status=status.HTTP_200_OK)

    @decorators.action(detail=False, methods=["post"], url_path="publish-due")
    def publish_due(self, request):
        from django.utils import timezone as djtz

        now = djtz.now()
        env = request.data.get("env", "dev")
        due_pages = Page.objects.filter(status="draft", publish_at__lte=now)
        published = []
        for page in due_pages:
            html = render_blocks(page.blocks_json or []) if page.blocks_json else (page.html or "")
            result = publish_page_assets(page.tenant_id, env, html, page.css or "", page.js or "")
            page.status = "published"
            page.rev = result.html_path.rsplit("/", 1)[-1]
            page.save(update_fields=["status", "rev"])
            PageRevision.objects.create(
                page=page,
                rev=page.rev,
                html=html,
                css=page.css or "",
                js=page.js or "",
                blocks_json=page.blocks_json or [],
            )
            published.append(page.id)
        return response.Response({"ok": True, "published": published}, status=status.HTTP_200_OK)
