# this_file: src/fontlab_fontport/paths.py
"""Explicit file locations, independent of FontLab's process working directory."""

from pathlib import Path


def absolute_path(path: str | Path, *, strict: bool = False) -> Path:
    target = Path(path)
    if not target.is_absolute():
        raise ValueError(
            "Path must be absolute; FontLab's working directory is not a default"
        )
    return target.resolve(strict=strict)
