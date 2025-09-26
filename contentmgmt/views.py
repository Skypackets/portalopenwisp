from django.shortcuts import render
from rest_framework import viewsets

from .models import Page
from .serializers import PageSerializer

# Create your views here.


class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all().order_by("-updated_at")
    serializer_class = PageSerializer
