"""
URL configuration for portalopenwisp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ads.views import CampaignViewSet, CreativeViewSet, EventViewSet, SlotViewSet
from contentmgmt.views import PageViewSet
from core.views import BrandViewSet, ControllerViewSet, SiteViewSet, SSIDViewSet, TenantViewSet
from analytics import views as analytics_views

router = DefaultRouter()
router.register(r"tenants", TenantViewSet)
router.register(r"brands", BrandViewSet)
router.register(r"sites", SiteViewSet)
router.register(r"ssids", SSIDViewSet)
router.register(r"controllers", ControllerViewSet)
router.register(r"pages", PageViewSet)
router.register(r"campaigns", CampaignViewSet)
router.register(r"creatives", CreativeViewSet)
router.register(r"slots", SlotViewSet)
router.register(r"events", EventViewSet)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("home.urls")),
    path("", include("portal.urls")),
    path("api/admin/", include(router.urls)),
    path("api/analytics/daily", analytics_views.daily_summary, name="analytics-daily"),
]
