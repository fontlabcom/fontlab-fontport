# this_file: src/fontlab_fontport/feature_blocks.py
"""Deprecated: use ``fontlabapp.fontui.feature_blocks`` instead.

Compatibility for shipped ``fly.fp.feature_blocks`` scripts. Importing this
module needs no App; accessing either helper requires ``fontlab-fontport[fontlab]``.
"""

from collections.abc import Callable
from typing import Any

read_feature_blocks: Callable[..., Any]
write_feature_blocks: Callable[..., Any]

__all__ = ["read_feature_blocks", "write_feature_blocks"]


def __getattr__(name: str):
    """Resolve a shipped helper lazily from its App home."""
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    return getattr(import_module("fontlabapp.fontui.feature_blocks"), name)


def __dir__():
    """Include the lazy compatibility helpers in module discovery."""
    return sorted(set(globals()) | set(__all__))
