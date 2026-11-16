# this_file: tests/native_drivers/fontport_owned.py
"""Host-side phased driver. Invoke via workspace fl-native.sh --mutating.

Each warm import, open, edit, Undo, Redo, save and reopen is a separate run_python
call. Timing receipts enforce a four-second phase budget below the host deadline.
Batch processing runs inside FontLab, one small UFO attempt per call, with
native document polls between calls. Restart FontLab after every mutating run;
the shared runner controls sessions but does not perform that restart.
"""

import hashlib
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from uuid import uuid4

from driver_args import arguments
from fontport_steps import phases

WIRE = """
import builtins, sys
saved_path = sys.path[:]
try:
    sys.path[:0] = added_paths
    runs = builtins.__dict__.setdefault("_fontport_native_runs", {})
    state = runs.setdefault(run_key, {"output": output_path, "paths": owned_paths, "origins": expected_origins, "run_key": run_key})
    exec(compile(phase_code, phase_name, "exec"), state)
    result = state.pop("result", None)
finally:
    sys.path[:] = saved_path
"""


def prepare(workspace: Path, output_root: Path) -> tuple[Path, dict, dict]:
    if not workspace.is_absolute() or not output_root.is_absolute():
        raise ValueError("Workspace and output root must be absolute")
    output = output_root / (
        datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid4().hex[:8]
    )
    output.mkdir(parents=True)
    corpus = workspace / "fontlab-python-examples/testdata/getgo/cc0"
    sources = {"medi": corpus / "medi/medi.vfj", "plum": corpus / "plum/plum-var.vfj"}
    hashes, owned = {}, {}
    for key, source in sources.items():
        hashes[str(source)] = hashlib.sha256(source.read_bytes()).hexdigest()
        target = output / (key + ".vfj")
        shutil.copy2(source, target)
        owned[key] = str(target)
    return output, owned, hashes


def run_suite(
    client,
    output: Path,
    owned: dict,
    sources: list[str],
    origins: dict,
    *,
    features_only: bool = False,
) -> dict:
    report = {
        "ok": False,
        "phases": [],
        "cleanup_errors": [],
        "acceptance_failures": [],
    }
    run_key = uuid4().hex
    started = False

    def step(name, code):
        before = monotonic()
        reply = client.run(
            WIRE,
            run_key=run_key,
            output_path=str(output),
            owned_paths=owned,
            added_paths=sources,
            expected_origins=origins,
            phase_code=code,
            phase_name=name,
        )
        elapsed = monotonic() - before
        report["phases"].append(
            {"name": name, "seconds": elapsed, "result": reply.value}
        )
        if (
            name.startswith("lib-")
            and isinstance(reply.value, dict)
            and reply.value.get("exact") is False
        ):
            report["acceptance_failures"].append({"name": name, "result": reply.value})
        if (
            name.startswith("feature-")
            and isinstance(reply.value, dict)
            and any(
                reply.value.get(flag) is False
                for flag in (
                    "supported",
                    "rows_equal",
                    "whole_text_equal",
                    "classes_equal",
                    "has_named_features",
                    "edit_available",
                    "no_history_for_identical_blocks",
                    "identical_write_succeeded",
                    "only_arbitrary_split_refused",
                    "no_history_for_split_refusal",
                    "implicit_languagesystem_refused",
                    "no_history_for_synthesis_refusal",
                )
            )
        ):
            report["acceptance_failures"].append({"name": name, "result": reply.value})
        if elapsed >= 4:
            raise RuntimeError(
                f"Phase {name} exceeded the 4 s budget; split further before rerunning"
            )

    try:
        if client.fonts():
            raise RuntimeError("Requires a dedicated no-document session")
        started = True
        selected = phases(features_only=True) if features_only else phases()
        for name, code in selected:
            step(name, code)
            if name.startswith("batch-"):
                before = monotonic()
                documents = client.fonts()
                elapsed = monotonic() - before
                report["phases"].append(
                    {
                        "name": name + "-host-poll",
                        "seconds": elapsed,
                        "result": documents,
                    }
                )
                if elapsed >= 4:
                    raise RuntimeError(
                        f"Native poll after {name} exceeded the 4 s budget"
                    )
        report["ok"] = True
    except Exception as error:  # noqa: BLE001 - retain the original failure alongside cleanup
        report["error"] = f"{type(error).__name__}: {error}"
    finally:
        if started:
            for name, code in (
                (
                    "batch-cleanup",
                    "for key in ('batch_jobs', 'batch_cancel'):\n    if key in globals(): globals()[key].close()",
                ),
                ("ui-cleanup", "if 'session' in globals(): session.close()"),
                (
                    "ui-after-event-loop",
                    "result = {'event_loop_returned': True, 'windows_retained': len(session._windows) if 'session' in globals() else 0}",
                ),
            ):
                try:
                    step(name, code)
                except Exception as error:  # noqa: BLE001 - record, never mask the original
                    report["cleanup_errors"].append(f"{name}: {error}")
            try:
                for row in client.fonts():
                    client.close_font(font_id=row["id"], save=False)
                report["fonts_left"] = client.fonts()
            except Exception as error:  # noqa: BLE001 - record, never mask the original
                report["cleanup_errors"].append(f"documents: {error}")
            if report["cleanup_errors"]:
                # Never GC a possibly live-slot widget after failed teardown.
                report["state_retained_for_restart"] = run_key
            else:
                try:
                    step(
                        "state-cleanup",
                        "import builtins\nbuiltins.__dict__.get('_fontport_native_runs', {}).pop(run_key, None)\nresult=True",
                    )
                except Exception as error:  # noqa: BLE001 - record, never mask the original
                    report["cleanup_errors"].append(f"state: {error}")
    report["ok"] = (
        report["ok"]
        and not report["cleanup_errors"]
        and not report.get("fonts_left")
        and not report["acceptance_failures"]
    )
    report["restart_required"] = True
    return report


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    args = arguments(root)
    if args.dry_run:
        print(
            json.dumps(
                {
                    "sources": args.sources,
                    "origins": args.origins,
                    "glyport": args.glyport,
                    "glyport_required": args.glyport_required,
                    "phases": [
                        name for name, _ in phases(features_only=args.features_only)
                    ],
                }
            )
        )
        return 0
    from fontlab_remopy import FontLab

    output, owned, hashes = prepare(args.workspace, args.output_root)
    with FontLab(timeout=30) as client:
        report = run_suite(
            client,
            output,
            owned,
            args.sources,
            args.origins,
            features_only=args.features_only,
        )
    report["source_hashes"] = hashes
    report["glyport"] = args.glyport
    report["glyport_required"] = args.glyport_required
    report["source_unchanged"] = all(
        hashlib.sha256(Path(path).read_bytes()).hexdigest() == value
        for path, value in hashes.items()
    )
    report["ok"] = report["ok"] and report["source_unchanged"]
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "ok": report["ok"],
                "receipt": str(output / "result.json"),
                "restart_required": True,
            }
        )
    )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
