from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def render_zone(context, zone_slug: str) -> str:
    # Minimal placeholder rendering; in production hook to selector
    return f'<div class="adzone" data-zone="{zone_slug}">Ad zone: {zone_slug}</div>'
