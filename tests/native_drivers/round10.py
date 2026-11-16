# this_file: tests/native_drivers/round10.py
"""C4-only controller: phased RPCs, owned copies, raw JSONL, explicit cleanup.

Dry-run/list modes never import Remopy or contact FontLab. Restart the dedicated
FontLab session after mutating runs. Python tracing limits Python work to 3 s;
a blocking native C++ call cannot be interrupted and must be ticketed/split if
its measured RPC reaches 4 s. No event-loop background work is scheduled.
"""

import argparse
import base64
import hashlib
import json
import plistlib
import shutil
from datetime import UTC, datetime
from importlib.machinery import PathFinder
from pathlib import Path
from time import monotonic
from uuid import uuid4

from round10_boundary_steps import phases as boundary_phases
from round10_common_steps import SETUP
from round10_glyph_steps import phases as glyph_phases
from round10_interchange_steps import compare_phases, import_phases, next_step, start
from round10_lifecycle_steps import phases as lifecycle_phases
from round10_pen_steps import phases as pen_phases
from round10_world_steps import phases as world_phases

WIRE = """
import builtins,sys,time,traceback
saved_path=sys.path[:]
previous_trace=sys.gettrace()
runs=builtins.__dict__.setdefault('_fontport_round10_runs',{})
state=runs.setdefault(run_key,{'output':output,'sources':sources,'owned_ids':set()})
deadline=time.monotonic()+3.0
def guard(frame,event,arg):
    if time.monotonic()>=deadline:
        raise RuntimeError('PhaseDeadline: Python phase exceeded 3 seconds')
    return guard
try:
    sys.path[:0]=sources
    sys.settrace(guard)
    try:
        exec(compile(code,phase,'exec'),state)
        result=state.pop('result',None)
    except Exception as error:
        sys.settrace(previous_trace)
        error_module=sys.modules.get('fontlab_fontport.errors')
        unsupported=getattr(error_module,'UnsupportedCapability',None)
        if unsupported is not None and isinstance(error,unsupported):
            result={'status':'UnsupportedCapability','capability':error.capability,'reason':str(error),'traceback':traceback.format_exc()}
        else:
            result={'status':'unclassified','phase_error':str(error),'type':type(error).__name__,'traceback':traceback.format_exc()}
    from round10_transfer import frame
    result=frame(result,state.setdefault('_reply_transfers',{}))
finally:
    sys.settrace(previous_trace)
    sys.path[:]=saved_path
"""


def arguments(argv=None):
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite",
        choices=(
            "upstream",
            "glyph",
            "world",
            "interchange",
            "pens",
            "boundaries",
            "lifecycle",
        ),
        required=True,
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=next(
            (
                p
                for p in root.parents
                if (p / "verification/issue-104/fl-native.sh").is_file()
            ),
            root,
        ),
    )
    parser.add_argument("--source", type=Path, action="append")
    parser.add_argument("--output-root", type=Path, default=root / ".local/round10")
    parser.add_argument(
        "--fixture", type=Path, help="Absolute GetGo VFJ; copied before opening"
    )
    parser.add_argument(
        "--test-id", action="append", help="Restrict upstream run; repeatable"
    )
    parser.add_argument(
        "--native-attached",
        action="store_true",
        help="Exercise all upstream families attached to owned native fonts",
    )
    parser.add_argument("--list-tests", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    args.root = root
    args.source = args.source or [
        root / "src",
        root / ".venv/lib/python3.11/site-packages",
    ]
    for path in [
        args.workspace,
        args.output_root,
        *args.source,
        *([args.fixture] if args.fixture else []),
    ]:
        if not path.is_absolute():
            parser.error(f"All paths must be absolute: {path}")
    spec = PathFinder.find_spec("fontlab_fontport", [str(p) for p in args.source])
    if spec is None or spec.origin is None:
        parser.error("fontlab_fontport unavailable in --source paths")
    args.origin = str(Path(spec.origin).resolve())
    args.source = [str(p.resolve()) for p in args.source]
    args.source += [str(root / "tests" / "native_drivers"), str(root / "examples/fontparts")]
    return args


class Run:
    def __init__(self, client, output, sources):
        self.client, self.output, self.sources = client, output, sources
        self.key = uuid4().hex
        self.failures = []
        self.receipts = output / "receipts.jsonl"

    def step(self, name, code):
        started = monotonic()
        reply = self.client.run(
            WIRE,
            run_key=self.key,
            output=str(self.output),
            sources=self.sources,
            code=code,
            phase=name,
        )
        elapsed = monotonic() - started
        value = reply.value
        if isinstance(value, dict) and set(value) == {"_fontport_transfer"}:
            from round10_transfer import CHUNK_SIZE, decode

            meta = value["_fontport_transfer"]
            parts = []
            for offset in range(0, meta["length"], CHUNK_SIZE):
                part = self.step(
                    name + "-chunk",
                    f"from round10_transfer import chunk\nresult=chunk(_reply_transfers,{meta['id']!r},{offset})",
                )
                if (
                    not isinstance(part, dict)
                    or part.get("offset") != offset
                    or not isinstance(part.get("data"), str)
                ):
                    raise RuntimeError(f"Invalid chunk for {name} at {offset}")
                parts.append(part["data"])
            value = decode(value, parts)
            self.step(
                name + "-release",
                f"_reply_transfers.pop({meta['id']!r},None)\nresult={{'released':True}}",
            )
        if isinstance(value, dict) and "payload" in value:
            from round10_payloads import COMPARISON_NOTES

            value["comparison_notes"] = COMPARISON_NOTES
        row = {"phase": name, "seconds": elapsed, "result": value}
        with self.receipts.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        if elapsed >= 4 or (
            isinstance(value, dict)
            and (
                value.get("status") == "unclassified"
                or (
                    name.startswith("example-")
                    and value.get("status") == "UnsupportedCapability"
                )
                or "phase_error" in value
                or any(
                    value.get(flag) is False
                    for flag in (
                        "equal",
                        "history_protocol_matches",
                        "geometry_equal",
                        "geometry_changed_when_required",
                        "capability_matches_expectation",
                        "has_undo_step",
                        "ok",
                        "digest_equal",
                        "bounds_equal",
                        "refusal_unchanged",
                        "control_unchanged",
                        "file_absent",
                        "prerequisite",
                    )
                )
            )
        ):
            self.failures.append(row)
        if elapsed >= 4:
            raise RuntimeError(
                f"{name} took {elapsed:.3f}s; split this phase before rerunning"
            )
        if name.endswith("-reopen") and (
            not isinstance(value, dict)
            or "phase_error" in value
            or value.get("status") in ("UnsupportedCapability", "unclassified")
            or value.get("equal") is False
        ):
            raise RuntimeError(f"Reopen failed: {name}; aborting suite")
        return value

    def phases(self, phases):
        save_failed = False
        for name, code in phases:
            dependent = name.endswith(
                ("-close", "-external-close", "-stale-reads", "-reopen", "-reopen-read")
            )
            if save_failed and dependent:
                self.step(
                    name,
                    "result={'skipped':'save refused or failed; keep document open'}",
                )
                continue
            value = self.step(name, code)
            if name.endswith("-save"):
                save_failed = (
                    not isinstance(value, dict)
                    or "path" not in value
                    or "phase_error" in value
                )
            self.step(
                name + "-poll",
                "result={'responsive':True,'fonts':fontpr.call('list_fonts')}",
            )


def collect_export(run, backend):
    """Assemble/save a real UFO outside FontLab; no bulk native disk write."""
    from fontTools.ufoLib.glifLib import readGlyphFromString
    from ufoLib2 import Font

    font = Font()
    default = backend
    if font.layers.defaultLayer.name != default:
        font.layers.renameLayer(font.layers.defaultLayer.name, default)
    run.step("export-start", start())
    while True:
        unit = run.step("export-next", next_step())
        if not isinstance(unit, dict) or "phase_error" in unit:
            raise RuntimeError("Export failed; retained raw phase receipt")
        if unit.get("status") == "UnsupportedCapability":
            from fontlab_fontport.errors import UnsupportedCapability

            raise UnsupportedCapability(unit["capability"], unit["reason"])
        if unit["complete"]:
            break
        kind = unit["kind"]
        if kind == "glyph":
            name = unit["layer"]
            layer = (
                font.layers[name] if name in font.layers else font.layers.newLayer(name)
            )
            glyph = layer.newGlyph(unit["name"])
            readGlyphFromString(unit["glif"], glyph, glyph.getPointPen())
        elif kind == "info":
            setattr(font.info, unit["name"], unit["value"])
        elif kind == "kerning":
            font.kerning = {tuple(pair): value for pair, value in unit["value"]}
        elif kind == "groups":
            font.groups = unit["value"]
        elif kind == "lib":
            font.lib = plistlib.loads(base64.b64decode(unit["value"]))
        elif kind == "features":
            font.features.text = unit["value"]
            font.lib = plistlib.loads(base64.b64decode(unit["lib_plist"]))
    path = run.output / "whole.ufo"
    font.save(path)
    return path


def run_upstream(run, identifiers, *, native_attached=False):
    run.step(
        "upstream-setup",
        "from fontlab_fontport.testing import ObjectGenerator,upstream_tests\nfrom upstream_steps import run_one,close_one\ngenerator=ObjectGenerator(native_attached=NATIVE_ATTACHED)\ncases={case.id():case for case in upstream_tests()}\nresult={'ready':True}".replace(
            "NATIVE_ATTACHED", repr(native_attached)
        ),
    )
    for identifier in identifiers:
        try:
            run.step(identifier, f"result=run_one({identifier!r},generator,cases)")
        finally:
            while True:
                remaining = run.step("upstream-cleanup", "result=close_one(generator)")
                if "phase_error" in remaining:
                    raise RuntimeError(
                        "Owned upstream cleanup failed; restart required"
                    )
                if not remaining["remaining"]:
                    break


def run_owned_families(run):
    families = (
        "font",
        "info",
        "groups",
        "kerning",
        "features",
        "lib",
        "layer",
        "glyph",
        "contour",
        "segment",
        "bPoint",
        "point",
        "component",
        "anchor",
        "guideline",
        "image",
    )
    run.step(
        "family-setup",
        "from fontlab_fontport.testing import ObjectGenerator\nfrom upstream_steps import close_one\ngenerator=ObjectGenerator(native_attached=True)\nresult={'ready':True}",
    )
    for family in families:
        try:
            run.step(
                "owned-family-" + family,
                f"try:\n    instance,unrequested=generator({family!r})\n    result={{'family':{family!r},'class':type(instance).__name__,'owners':[f._backend.font_id for f in generator.owned]}}\nexcept UnsupportedCapability as error:\n    result={{'family':{family!r},'capability':error.capability,'reason':str(error),'status':'UnsupportedCapability'}}",
            )
        finally:
            while True:
                value = run.step("family-cleanup", "result=close_one(generator)")
                if "phase_error" in value:
                    raise RuntimeError("Owned family cleanup failed")
                if not value["remaining"]:
                    break


def execute(client, args, output, identifiers):
    run = Run(client, output, args.source)
    if client.fonts():
        raise RuntimeError("Use a fresh dedicated FontLab session with no documents")
    try:
        example_modules = [
            path.stem for path in (args.root / "examples/fontparts").glob("[0-9]*.py")
        ]
        run.step(
            "source-reset",
            f"import sys\nfor key in list(sys.modules):\n    if key=='fontlab_fontport' or key.startswith('fontlab_fontport.') or key.startswith('round10_') or key in ('upstream_steps','_owned') or key in {example_modules!r}:\n        sys.modules.pop(key,None)\nresult={{'reset':True}}",
        )
        for module in (
            "fontlab_fontport",
            "defcon",
            "fontParts.fontshell",
            "ufoLib2",
            "fontlab_fontport.testing",
            "fontParts.test",
        ):
            value = run.step(
                "warm-" + module,
                f"import importlib\nm=importlib.import_module({module!r})\nresult={{'module':{module!r},'file':m.__file__}}",
            )
            if module == "fontlab_fontport" and value.get("file") != args.origin:
                raise RuntimeError(f"Wrong Fontport origin: {value}")
            if "phase_error" in value:
                raise RuntimeError(f"Warm import failed: {module}")
        run.step("setup", SETUP)
        if args.suite == "upstream":
            run_owned_families(run)
            run_upstream(run, identifiers, native_attached=args.native_attached)
            return run
        source = (
            args.fixture
            or args.workspace
            / "fontlab-python-examples/testdata/getgo/cc0/medi/medi.vfj"
        )
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        owned = output / "owned.vfj"
        shutil.copy2(source, owned)
        run.step(
            "owned-open",
            f"font=environment.OpenFont({str(owned)!r})\nbackend=font._backend\nowned_ids.add(backend.font_id)\nresult={{'id':backend.font_id}}",
        )
        for name in ("fontport_probe", "fontport_component", "fontport_flat"):
            run.step(
                "owned-create-" + name,
                f"font.newGlyph({name!r})\nresult={{'name':{name!r}}}",
            )
        if args.suite == "glyph":
            from round10_glyph_steps import hinted_phases

            names = run.step(
                "hinted-candidates",
                "result=list(backend.glyph_names(backend.default_layer()))",
            )
            if not isinstance(names, list) or not all(
                isinstance(n, str) for n in names
            ):
                raise RuntimeError("Hinted candidates failed: expected glyph-name list")
            run.phases(hinted_phases(names))
            run.phases(glyph_phases())
        elif args.suite == "world":
            shutil.copy2(source, output / "world-open.vfj")
            names = [
                p.stem
                for p in sorted((args.root / "examples/fontparts").glob("[0-9]*.py"))
            ]
            run.phases(world_phases(names))
        elif args.suite == "boundaries":
            run.phases(boundary_phases())
        elif args.suite == "lifecycle":
            run.phases(lifecycle_phases())
        elif args.suite == "pens":
            from fontPens.flattenPen import FlattenPen
            from fontTools.pens.recordingPen import DecomposingRecordingPen
            from fontTools.pens.roundingPen import RoundingPen
            from ufoLib2 import Font
            from ufoLib2.objects import Glyph

            from fontlab_fontport.recipes import digest as point_digest

            default = run.step("pens-export-default", "result=backend.default_layer()")
            export_path = collect_export(run, default)
            with Font.open(export_path) as exported:
                expected_digests = {g.name: point_digest(g) for g in exported}
                recording = DecomposingRecordingPen(exported)
                exported["A"].draw(recording)
                expected_flat = Glyph("fontport_flat")
                recording.replay(
                    FlattenPen(
                        RoundingPen(expected_flat.getPen()), approximateSegmentLength=10
                    )
                )
                flatten_digest = point_digest(expected_flat)
            names = run.step("pens-names", "result=list(font.keys())")
            run.phases(pen_phases(names, expected_digests, flatten_digest))
        elif args.suite == "interchange":
            default = run.step("export-default", "result=backend.default_layer()")
            path = collect_export(run, default)
            run.phases(import_phases(path))
            complete = False
            while not complete:
                value = run.step(
                    "import-preflight",
                    "try:\n    unit=next(import_checks)\n    result={'complete':False,'unit':unit}\nexcept StopIteration:\n    result={'complete':True}\nexcept UnsupportedCapability as error:\n    result={'complete':True,'refused':True,'capability':error.capability,'reason':str(error)}",
                )
                complete = value.get("complete", True)
            if not value.get("refused") and "phase_error" not in value:
                run.step(
                    "import-allocate",
                    "imported,import_steps=import_plan.begin(create_owned_backend)\nresult={'allocated':True}",
                )
                while True:
                    value = run.step(
                        "import-next",
                        "try:\n    result={'complete':False,'unit':next(import_steps)}\nexcept StopIteration:\n    result={'complete':True}",
                    )
                    if value.get("complete") or "phase_error" in value:
                        break
                if "phase_error" not in value:
                    names = run.step(
                        "import-names", "result=list(import_plan.staged.keys())"
                    )
                    run.phases(compare_phases(names, "import-compare"))
                    saved = run.step(
                        "import-save",
                        "import_path=str(Path(output)/'imported.vfj')\nimported.save(import_path)\nresult={'path':import_path}",
                    )
                    if (
                        isinstance(saved, dict)
                        and "path" in saved
                        and "phase_error" not in saved
                    ):
                        run.step(
                            "import-close", "imported.close()\nresult={'closed':True}"
                        )
                        run.step(
                            "import-reopen",
                            "imported=environment.OpenFont(import_path)\nowned_ids.add(imported._backend.font_id)\nresult={'id':imported._backend.font_id}",
                        )
                        run.phases(compare_phases(names, "import-reopen-compare"))
        observed_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        run.step(
            "source-unchanged",
            f"result={{'equal':{observed_hash == digest!r},'source_sha256':{digest!r},'observed_sha256':{observed_hash!r}}}",
        )
        if observed_hash != digest:
            raise RuntimeError("Original corpus source changed")
    except Exception as error:  # noqa: BLE001 - retain terminal failures with receipts
        import traceback

        from fontlab_fontport.errors import UnsupportedCapability

        run.failures.append(
            {
                "status": "UnsupportedCapability"
                if isinstance(error, UnsupportedCapability)
                else "unclassified",
                "terminal_error": str(error),
                "traceback": traceback.format_exc(),
            }
        )
    finally:
        # Cleanup reads only the IDs this run recorded as owned. No assertions,
        # forced deferred deletes or user-document close calls in finally.
        for label, code in (
            (
                "native-fixture-references",
                "for key in ('legacy_plain','legacy_values','legacy_before','native_kern'):\n    globals().pop(key,None)\nresult={'released_before_document_close':True}",
            ),
            (
                "world-cleanup",
                "if 'registration' in globals():\n    registration.close()\nresult={'unregistered':True}",
            ),
            (
                "import-cleanup",
                "if 'import_context' in globals():\n    import_context.__exit__(None,None,None)\nif 'import_source' in globals():\n    import_source.close()\nresult={'closed':True}",
            ),
            (
                "upstream-finally",
                "if 'generator' in globals():\n    owned_ids.update(generator.pending_ids)\nresult={'tracked':True}",
            ),
        ):
            try:
                run.step(label, code)
            except Exception as error:  # noqa: BLE001 - never skip document cleanup
                run.failures.append({"cleanup": label, "error": str(error)})
        ids = []
        try:
            ids = run.step("owned-ids", "result=list(owned_ids)")
        except Exception as error:  # noqa: BLE001 - retain tracking failure
            run.failures.append({"cleanup": "owned-ids", "error": str(error)})
        if isinstance(ids, list):
            for identifier in ids:
                try:
                    if any(row["id"] == identifier for row in client.fonts()):
                        client.close_font(font_id=identifier, save=False)
                except Exception as error:  # noqa: BLE001 - retain cleanup failure
                    run.failures.append({"cleanup_id": identifier, "error": str(error)})
        try:
            run.step(
                "drop-state",
                "import builtins\nbuiltins.__dict__.get('_fontport_round10_runs',{}).pop("
                + repr(run.key)
                + ",None)\nresult={'dropped':True}",
            )
        except Exception as error:  # noqa: BLE001 - report failure without masking
            run.failures.append({"cleanup": "drop-state", "error": str(error)})
    return run


def main(argv=None):
    args = arguments(argv)
    identifiers = []
    if args.suite == "upstream":
        from fontlab_fontport.testing import upstream_tests

        identifiers = [case.id() for case in upstream_tests()]
        if args.test_id:
            unknown = set(args.test_id) - set(identifiers)
            if unknown:
                raise ValueError(f"Unknown upstream IDs: {sorted(unknown)}")
            identifiers = args.test_id
    if args.dry_run or args.list_tests:
        print(
            json.dumps(
                {
                    "suite": args.suite,
                    "sources": args.source,
                    "origin": args.origin,
                    "test_ids": identifiers,
                    "native_contacted": False,
                    "upstream_mode": "attached" if args.native_attached else "orphan",
                }
            )
        )
        return 0
    from fontlab_remopy import FontLab

    output = args.output_root / (
        datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid4().hex[:8]
    )
    output.mkdir(parents=True)
    with FontLab(timeout=30) as client:
        run = execute(client, args, output, identifiers)
    from collections import Counter

    upstream_counts = Counter()
    for line in run.receipts.read_text().splitlines():
        value = json.loads(line).get("result")
        if isinstance(value, dict) and "id" in value and "status" in value:
            upstream_counts[value["status"]] += 1
    result = {
        "upstream_counts": dict(upstream_counts),
        "ok": not run.failures,
        "failures": run.failures,
        "receipts": str(run.receipts),
        "restart_required": True,
    }
    (output / "result.json").write_text(
        json.dumps(result, indent=2, default=str) + "\n"
    )
    print(
        json.dumps({key: value for key, value in result.items() if key != "failures"})
    )
    return int(bool(run.failures))


if __name__ == "__main__":
    raise SystemExit(main())
