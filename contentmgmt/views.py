from rest_framework import decorators, response, status, viewsets

from core.views import _get_request_tenant_id

from .models import Page
from .serializers import PageSerializer
from .utils import publish_page_assets


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
        result = publish_page_assets(
            page.tenant_id, env, page.html or "", page.css or "", page.js or ""
        )
        page.status = "published"
        page.rev = result.html_path.rsplit("/", 1)[-1]
        page.save(update_fields=["status", "rev"])
        return response.Response(
            {
                "ok": True,
                "html_path": result.html_path,
                "css_path": result.css_path,
                "js_path": result.js_path,
            },
            status=status.HTTP_200_OK,
        )
