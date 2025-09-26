from rest_framework import decorators, response, status, viewsets

from .models import Page
from .serializers import PageSerializer
from .utils import publish_page_assets


class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all().order_by("-updated_at")
    serializer_class = PageSerializer

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
