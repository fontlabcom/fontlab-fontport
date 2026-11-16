# this_file: src/fontlab_fontport/deploy.py
"""Generate an opt-in FontParts launcher at an explicit caller-owned path."""

from pathlib import Path

from .paths import absolute_path


def write_launcher(
    destination: str | Path, *, source: str | Path | None = None
) -> Path:
    """Create a startup script, never a run_python payload or app-folder install."""
    target = absolute_path(destination)
    source = absolute_path(source, strict=True) if source is not None else None
    lines = [
        "# this_file: " + target.name,
        "# Generated Fontport startup launcher; do not send through run_python.",
        "# Requires installed fontlab-fly>=1.3.0 and its canonical providers.",
    ]
    if source is not None:
        lines += ["import sys", f"sys.path.insert(0, {str(source)!r})"]
    lines += ["import fly.fp as fontlab_fontport", "from pathlib import Path"]
    if source is not None:
        lines += [
            f"if not Path(fontlab_fontport.__file__).resolve().is_relative_to(Path({str(source)!r})):",
            "    raise RuntimeError('A different Fontport is already loaded; restart FontLab before launching')",
        ]
    lines += [
        "from fly.fp.world import register",
        "fontport_registration = register()",
        "# fontport_registration.close() restores the previous environment.",
    ]
    with target.open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")
    return target
