from rest_framework import serializers

from .models import SSID, Brand, Controller, Site, Tenant


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = "__all__"


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = "__all__"


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = "__all__"


class SSIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = SSID
        fields = "__all__"


class ControllerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Controller
        fields = "__all__"
