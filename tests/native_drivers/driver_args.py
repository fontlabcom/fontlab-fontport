# this_file: tests/native_drivers/driver_args.py
"""Resolve CLI sources in the invoking shell, before connecting to FontLab."""

import argparse
from importlib.machinery import PathFinder
from pathlib import Path


def arguments(root: Path, argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=root.parents[1])
    parser.add_argument(
        "--output-root", type=Path, default=root / ".local/native-issue105"
    )
    parser.add_argument(
        "--source",
        type=Path,
        action="append",
        help="Replace default import roots; repeat for installed-artifact runs",
    )
    parser.add_argument(
        "--extra-source",
        type=Path,
        action="append",
        default=[],
        help="Add an import root before dependency site-packages (e.g. Glyport src)",
    )
    parser.add_argument(
        "--require-glyport",
        action="store_true",
        help="Fail unless Glyport resolves; without it Glyport is recorded only when present",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate paths/module origins; do not connect or write fixtures",
    )
    parser.add_argument(
        "--features-only",
        action="store_true",
        help="Run B08 in isolation, including separate Medio/Plum metadata timings",
    )
    args = parser.parse_args(argv)
    defaults = [root / "src", root / ".venv/lib/python3.11/site-packages"]
    sources = args.source or [defaults[0], *args.extra_source, defaults[1]]
    if args.source:
        sources = [*sources, *args.extra_source]
    # CLI paths belong to this external process, never FontLab's implicit cwd.
    args.sources = [str(path.resolve()) for path in sources]
    args.workspace, args.output_root = (
        args.workspace.resolve(),
        args.output_root.resolve(),
    )
    args.origins = {}
    for name in ("fontlab_fontport", "fontlab_glyport"):
        spec = PathFinder.find_spec(name, args.sources)
        if spec is None or spec.origin is None:
            if name == "fontlab_glyport" and not args.require_glyport:
                continue  # no phase imports Glyport; the purge list still names it
            parser.error(
                f"Cannot locate {name} in supplied sources; add --extra-source"
            )
        args.origins[name] = str(Path(spec.origin).resolve())
    # Receipts say whether Glyport was checked: None means skipped, never "absent from the run".
    args.glyport = args.origins.get("fontlab_glyport")
    args.glyport_required = bool(args.require_glyport)
    return args
