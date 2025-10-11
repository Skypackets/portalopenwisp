from __future__ import annotations

from typing import Dict, List

import bleach


def render_blocks(blocks: List[Dict]) -> str:
    parts: List[str] = []
    for block in blocks or []:
        t = block.get("type")
        if t == "hero":
            title = bleach.clean(block.get("title", ""))
            subtitle = bleach.clean(block.get("subtitle", ""))
            parts.append(f"<section class='hero'><h1>{title}</h1><p>{subtitle}</p></section>")
        elif t == "paragraph":
            text = bleach.clean(block.get("text", ""))
            parts.append(f"<p>{text}</p>")
        elif t == "button":
            label = bleach.clean(block.get("label", ""))
            href = bleach.clean(block.get("href", "#"))
            parts.append(f"<a class='btn' href='{href}'>{label}</a>")
        elif t == "ad_slot":
            slot = bleach.clean(block.get("slot", "hero"))
            parts.append(f"<div id='ad-slot-{slot}' data-slot='{slot}'></div>")
        else:
            continue
    return "\n".join(parts)
