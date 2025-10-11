from rest_framework import viewsets

from core.views import _get_request_tenant_id

from .models import Campaign, Creative, Event, Slot
from .serializers import CampaignSerializer, CreativeSerializer, EventSerializer, SlotSerializer

# Create your views here.


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all().order_by("-updated_at")
    serializer_class = CampaignSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = _get_request_tenant_id(self.request)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        return qs


class CreativeViewSet(viewsets.ModelViewSet):
    queryset = Creative.objects.all().order_by("-updated_at")
    serializer_class = CreativeSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = _get_request_tenant_id(self.request)
        if tenant_id:
            qs = qs.filter(campaign__tenant_id=tenant_id)
        campaign_id = self.request.query_params.get("campaign_id") if hasattr(self.request, "query_params") else None
        if campaign_id and campaign_id.isdigit():
            qs = qs.filter(campaign_id=int(campaign_id))
        return qs


class SlotViewSet(viewsets.ModelViewSet):
    queryset = Slot.objects.all().order_by("-updated_at")
    serializer_class = SlotSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = _get_request_tenant_id(self.request)
        if tenant_id:
            qs = qs.filter(page__tenant_id=tenant_id)
        page_id = self.request.query_params.get("page_id") if hasattr(self.request, "query_params") else None
        if page_id and page_id.isdigit():
            qs = qs.filter(page_id=int(page_id))
        return qs


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Event.objects.all().order_by("-created_at")
    serializer_class = EventSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        tenant_id = _get_request_tenant_id(self.request)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        return qs
