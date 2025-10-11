from __future__ import annotations

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render


def home(request):
    return render(
        request, "home.html", {"app_name": "Sky Packets Portal", "hero_zone_slug": "hero"}
    )


@staff_member_required
def builder(request):
    return render(request, "builder.html")
