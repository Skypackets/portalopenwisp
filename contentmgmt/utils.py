import hashlib
from dataclasses import dataclass
from typing import Dict

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


@dataclass
class PublishResult:
    html_path: str
    css_path: str | None
    js_path: str | None


def _hash_content(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:16]


def publish_page_assets(
    tenant_id: int, env: str, html: str, css: str = "", js: str = ""
) -> PublishResult:
    base_prefix = f"cp/{tenant_id}/{env}/pages/"
    html_bytes = html.encode("utf-8")
    html_hash = _hash_content(html_bytes)
    html_path = f"{base_prefix}page-{html_hash}.html"
    default_storage.save(html_path, ContentFile(html_bytes))

    css_path = None
    js_path = None
    if css:
        css_bytes = css.encode("utf-8")
        css_hash = _hash_content(css_bytes)
        css_path = f"{base_prefix}style-{css_hash}.css"
        default_storage.save(css_path, ContentFile(css_bytes))
    if js:
        js_bytes = js.encode("utf-8")
        js_hash = _hash_content(js_bytes)
        js_path = f"{base_prefix}script-{js_hash}.js"
        default_storage.save(js_path, ContentFile(js_bytes))

    return PublishResult(html_path=html_path, css_path=css_path, js_path=js_path)
