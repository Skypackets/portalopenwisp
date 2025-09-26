from rest_framework import viewsets

from .models import Campaign, Creative, Event, Slot
from .serializers import CampaignSerializer, CreativeSerializer, EventSerializer, SlotSerializer

# Create your views here.


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all().order_by("-updated_at")
    serializer_class = CampaignSerializer


class CreativeViewSet(viewsets.ModelViewSet):
    queryset = Creative.objects.all().order_by("-updated_at")
    serializer_class = CreativeSerializer


class SlotViewSet(viewsets.ModelViewSet):
    queryset = Slot.objects.all().order_by("-updated_at")
    serializer_class = SlotSerializer


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Event.objects.all().order_by("-created_at")
    serializer_class = EventSerializer
