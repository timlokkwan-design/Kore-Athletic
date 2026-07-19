"""Optional streamlit-extras stylable_container — falls back if package missing.

IMPORTANT: streamlit-extras prefixes `.st-key-…` once per *list item*.
A multi-rule CSS *string* only scopes the first rule; later selectors
(`div[data-testid="stHorizontalBlock"]`, `button`, …) leak page-wide and
can force calendar week rows into `nowrap`, blowing past the viewport.
"""

from __future__ import annotations

import re
from contextlib import contextmanager
from typing import Iterator


try:
    from streamlit_extras.stylable_container import (
        stylable_container as _stylable_container,
    )

    HAS_STYLABLE = True
except ImportError:
    HAS_STYLABLE = False


def _strip_css_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def split_css_blocks(css_styles: str | list[str]) -> list[str]:
    """Split CSS into top-level rule blocks for safe stylable_container scoping."""
    if isinstance(css_styles, list):
        out: list[str] = []
        for item in css_styles:
            out.extend(split_css_blocks(item))
        return out

    css = _strip_css_comments(css_styles).strip()
    if not css:
        return []

    blocks: list[str] = []
    depth = 0
    start = 0
    for i, ch in enumerate(css):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                block = css[start : i + 1].strip()
                if block:
                    blocks.append(block)
                start = i + 1
    tail = css[start:].strip()
    if tail:
        blocks.append(tail)
    return blocks or [css]


@contextmanager
def stylable_container(*, key: str, css_styles: str | list[str]) -> Iterator[None]:
    blocks = split_css_blocks(css_styles)
    if HAS_STYLABLE:
        with _stylable_container(key=key, css_styles=blocks or [""]):
            yield
    else:
        yield
