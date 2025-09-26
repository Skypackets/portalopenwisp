from django.shortcuts import render
from rest_framework import filters, viewsets

from .models import SSID, Brand, Controller, Site, Tenant
from .serializers import (
    BrandSerializer,
    ControllerSerializer,
    SiteSerializer,
    SSIDSerializer,
    TenantSerializer,
)

# Create your views here.


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all().order_by("-created_at")
    serializer_class = TenantSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all().order_by("-created_at")
    serializer_class = BrandSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all().order_by("-created_at")
    serializer_class = SiteSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class SSIDViewSet(viewsets.ModelViewSet):
    queryset = SSID.objects.all().order_by("-created_at")
    serializer_class = SSIDSerializer


class ControllerViewSet(viewsets.ModelViewSet):
    queryset = Controller.objects.all().order_by("-created_at")
    serializer_class = ControllerSerializer
