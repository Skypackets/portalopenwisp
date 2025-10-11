from rest_framework import filters, viewsets

from .models import SSID, Brand, Controller, Site, Tenant
from .serializers import (
    BrandSerializer,
    ControllerSerializer,
    SiteSerializer,
    SSIDSerializer,
    TenantSerializer,
)


def _get_request_tenant_id(request) -> int | None:
    """Return tenant id from header or query param if provided."""
    tenant_header = request.headers.get("X-Tenant-ID")
    if tenant_header and tenant_header.isdigit():
        return int(tenant_header)
    tenant_param = (
        request.query_params.get("tenant_id") if hasattr(request, "query_params") else None
    )
    if tenant_param and tenant_param.isdigit():
        return int(tenant_param)
    return None

# Create your views here.


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all().order_by("-created_at")
    serializer_class = TenantSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = _get_request_tenant_id(self.request)
        if tenant_id:
            qs = qs.filter(id=tenant_id)
        return qs


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all().order_by("-created_at")
    serializer_class = BrandSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = _get_request_tenant_id(self.request)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        return qs


class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all().order_by("-created_at")
    serializer_class = SiteSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = _get_request_tenant_id(self.request)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        return qs


class SSIDViewSet(viewsets.ModelViewSet):
    queryset = SSID.objects.all().order_by("-created_at")
    serializer_class = SSIDSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = _get_request_tenant_id(self.request)
        if tenant_id:
            qs = qs.filter(site__tenant_id=tenant_id)
        site_id = (
            self.request.query_params.get("site_id")
            if hasattr(self.request, "query_params")
            else None
        )
        if site_id and site_id.isdigit():
            qs = qs.filter(site_id=int(site_id))
        return qs


class ControllerViewSet(viewsets.ModelViewSet):
    queryset = Controller.objects.all().order_by("-created_at")
    serializer_class = ControllerSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = _get_request_tenant_id(self.request)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        return qs
