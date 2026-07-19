"""Optional streamlit-extras stylable_container — falls back if package missing."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

try:
    from streamlit_extras.stylable_container import (
        stylable_container as _stylable_container,
    )

    HAS_STYLABLE = True
except ImportError:
    HAS_STYLABLE = False


@contextmanager
def stylable_container(*, key: str, css_styles: str) -> Iterator[None]:
    if HAS_STYLABLE:
        with _stylable_container(key=key, css_styles=css_styles):
            yield
    else:
        yield
