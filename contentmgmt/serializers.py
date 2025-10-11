from rest_framework import serializers

from .models import Page, PageRevision


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = "__all__"


class PageRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageRevision
        fields = "__all__"
