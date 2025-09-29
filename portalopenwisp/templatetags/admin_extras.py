from django import template
from django.apps import apps

register = template.Library()


@register.simple_tag
def model_count(model_path: str) -> int:
    try:
        app_label, model_name = model_path.split(".")
        model = apps.get_model(app_label, model_name)
        return model.objects.count()
    except Exception:
        return 0


@register.simple_tag
def model_count2(app_label: str, object_name: str) -> int:
    try:
        model = apps.get_model(app_label, object_name)
        return model.objects.count()
    except Exception:
        return 0
