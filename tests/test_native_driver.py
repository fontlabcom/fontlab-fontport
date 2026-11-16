# this_file: tests/test_native_driver.py
"""Driver orchestration and executable B05/B10/B09 coverage without native calls."""

import ast
import json
import runpy
import shlex
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_native_features import native_features as shared_native_features

native_features = shared_native_features


@pytest.fixture
def driver(monkeypatch):
    folder = Path(__file__).resolve().parents[1] / "tests" / "native_drivers"
    monkeypatch.syspath_prepend(str(folder))
    return runpy.run_path(str(folder / "fontport_owned.py"), run_name="driver_test")


def test_driver_when_phases_compiled_then_each_warm_and_heavy_operation_is_separate(
    driver,
):
    phases = list(driver["phases"]())
    for name, code in phases:
        compile(code, name, "exec")
        tree = ast.parse(code)
        operations = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in ("OpenFont", "save", "close")
        ]
        assert len(operations) <= 2, (
            name
        )  # idempotent UI close is intentionally repeated.
    names = [name for name, _ in phases]
    assert [name for name in names if name.startswith("warm-")][:3] == [
        "warm-defcon",
        "warm-fontParts.world",
        "warm-ufoLib2",
    ]
    assert "info-openTypeOS2Panose-undo-readback" in names
    assert "info-postscriptStemSnapV-reopen-readback" in names
    assert "lib-clear" in names and "lib-identical-noop" in names
    assert not any(name.startswith("vanilla-") for name in names)


def test_driver_when_two_runs_prepared_then_unique_owned_copies_and_unchanged_sources(
    driver, tmp_path
):
    corpus = tmp_path / "fontlab-python-examples/testdata/getgo/cc0"
    for relative in ("medi/medi.vfj", "plum/plum-var.vfj"):
        path = corpus / relative
        path.parent.mkdir(parents=True)
        path.write_bytes(b"owned fixture")
    first, paths, hashes = driver["prepare"](tmp_path, tmp_path / "output")
    second, _, _ = driver["prepare"](tmp_path, tmp_path / "output")
    assert first != second and first.is_dir() and second.is_dir()
    assert all(Path(path).read_bytes() == b"owned fixture" for path in paths.values())
    assert all(Path(path).read_bytes() == b"owned fixture" for path in hashes)


def test_driver_when_phase_and_cleanup_fail_then_original_error_is_retained(
    driver, tmp_path
):
    class Client:
        def fonts(self):
            return []

        def run(self, code, **kwargs):
            if kwargs.get("phase_name") == "warm-defcon":
                raise ValueError("original phase failure")
            if kwargs.get("phase_name") == "ui-cleanup":
                raise RuntimeError("cleanup failure")
            return SimpleNamespace(value=True)

    result = driver["run_suite"](Client(), tmp_path, {}, [], {})
    assert result["error"] == "ValueError: original phase failure"
    assert "cleanup failure" in result["cleanup_errors"][0] and not result["ok"]
    assert result["state_retained_for_restart"], (
        "live slots must remain strongly owned after cleanup failure"
    )
    tree = ast.parse(Path(driver["__file__"]).read_text())
    assert not any(
        isinstance(node, ast.Assert)
        for item in ast.walk(tree)
        if isinstance(item, ast.Try)
        for part in item.finalbody
        for node in ast.walk(part)
    )


def test_batch_driver_when_native_steps_then_geometry_progress_failure_and_polling(
    driver, tmp_path
):
    from batch_driver import batch_phases
    from test_operations import fixture_font

    fixture_font().save(tmp_path / "source.ufo")
    state = {"output": str(tmp_path)}
    receipts = {}
    for name, code in batch_phases():
        exec(compile(code, name, "exec"), state)
        receipts[name] = state.pop("result", None)
    assert receipts["batch-poll-1"] == {"running": True, "attempts": 1}
    assert receipts["batch-poll-2"] == {"running": True, "attempts": 2}
    assert (tmp_path / "batch-output.ufo").is_dir()
    results = json.loads((tmp_path / "batch-results.json").read_text())
    assert results[0]["ok"] and not results[1]["ok"]
    assert not state["batch_runner"].running


def test_driver_when_manifest_command_dry_run_then_glyport_source_resolves(
    driver, tmp_path
):
    root = Path(driver["__file__"]).parents[2]
    manifest = json.loads(
        (root / "verification/issue-105/NATIVE-MANIFEST.json").read_text()
    )
    # The frozen manifest records the drivers' pre-issue-205 home.
    recorded = manifest["probe_command_from_workspace"]
    command = shlex.split(recorded.replace("/native-drivers/", "/tests/native_drivers/"))
    script_index = next(
        i for i, part in enumerate(command) if part.endswith("fontport_owned.py")
    )
    # Reproduce the workspace layout, including the command's explicit Glyport path.
    (tmp_path / ".worktrees").mkdir()
    (tmp_path / ".worktrees/issue-105-fontport").symlink_to(
        root, target_is_directory=True
    )
    glyport = tmp_path / "fontlab-glyport/src/fontlab_glyport"
    glyport.mkdir(parents=True)
    (glyport / "__init__.py").write_text("")
    result = subprocess.run(
        [sys.executable, *command[script_index:], "--dry-run"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["origins"]["fontlab_glyport"] == str(glyport / "__init__.py")
    assert receipt["origins"]["fontlab_fontport"] == str(
        root / "src/fontlab_fontport/__init__.py"
    )
    assert receipt["sources"][0] == str(root / "src")
    assert receipt["glyport"] == receipt["origins"]["fontlab_glyport"]
    assert receipt["glyport_required"] is False, "the frozen command does not pass --require-glyport"
    assert not (root / ".local/native-issue105/dry-run").exists()


def test_driver_when_foreign_probe_rounds_then_records_and_continues(driver):
    package = SimpleNamespace(packageLib={})
    state = {"backend": SimpleNamespace(_package=lambda: package)}
    code = dict(driver["phases"]())["lib-foreign-probes"]

    # Model a QVariant JSON bridge that rounds integers and CRLF text.
    class Package:
        @property
        def packageLib(self):
            return {
                key: float(value) if type(value) is int else value
                for key, value in package.packageLib.items()
            }

        @packageLib.setter
        def packageLib(self, value):
            package.packageLib = value

    state["backend"]._package = Package
    state["backend"].get_lib = lambda: Package().packageLib
    exec(compile(code, "foreign-probe", "exec"), state)
    assert not state["result"]["exact"]
    assert "fontport.probe.big" in state["result"]["mismatches"]


def test_driver_when_native_phases_then_no_forced_event_deletion_and_both_packages_purged(
    driver,
):
    codes = dict(driver["phases"]())
    source = Path(driver["__file__"]).read_text() + "\n".join(codes.values())
    assert "sendPostedEvents" not in source
    purge = codes["purge-stale-project-modules"]
    fake_sys = SimpleNamespace(
        modules={
            "fontlab_fontport": object(),
            "fontlab_fontport.world": object(),
            "fontlab_glyport": object(),
            "fontlab_glyport.ui.session": object(),
            "fontlab_glyport_other": object(),
        }
    )
    exec(compile(purge.replace("import sys", ""), "purge", "exec"), {"sys": fake_sys})
    assert list(fake_sys.modules) == ["fontlab_glyport_other"]


def test_driver_when_native_batch_phases_then_calls_and_host_polls_interleave(
    driver, tmp_path, monkeypatch
):
    from batch_driver import batch_phases
    from test_operations import fixture_font

    fixture_font().save(tmp_path / "source.ufo")
    monkeypatch.setitem(driver["run_suite"].__globals__, "phases", batch_phases)
    events, state = [], {"output": str(tmp_path), "run_key": "host-free-test"}

    class Client:
        def fonts(self):
            events.append("poll")
            return []

        def run(self, code, **kwargs):
            name = kwargs.get("phase_name")
            if name:
                events.append(name)
                exec(compile(kwargs["phase_code"], name, "exec"), state)
                value = state.pop("result", None)
                json.dumps(
                    value
                )  # RPC receipts contain JSON scalars, never Path objects.
                return SimpleNamespace(value=value)
            return SimpleNamespace(value=True)

    report = driver["run_suite"](Client(), tmp_path, {}, [], {})
    assert report["ok"], report
    for index, name in enumerate(events):
        if name.startswith("batch-") and name != "batch-cleanup":
            assert events[index + 1] == "poll", (
                "each batch call must return before a native heartbeat"
            )
    assert all(item["seconds"] < 4 for item in report["phases"])


def test_driver_when_source_missing_then_preflight_refuses_before_connection(
    driver, tmp_path
):
    from driver_args import arguments

    with pytest.raises(SystemExit) as error:
        arguments(
            Path(driver["__file__"]).parents[2],
            ["--source", str(tmp_path), "--dry-run"],
        )
    assert error.value.code == 2


def test_driver_when_stale_import_origin_then_warm_phase_refuses(driver):
    code = dict(driver["phases"]())["warm-fontlab_fontport.world"]
    with pytest.raises(AssertionError):
        exec(
            compile(code, "warm-origin", "exec"),
            {"origins": {"fontlab_fontport": "/wrong/installed/path.py"}},
        )


def test_driver_when_phase_exceeds_budget_then_reports_failure(
    driver, tmp_path, monkeypatch
):
    from itertools import count

    globals_ = driver["run_suite"].__globals__
    monkeypatch.setitem(globals_, "phases", lambda: iter([("slow-operation", "")]))
    clock = count(step=4.1)
    monkeypatch.setitem(globals_, "monotonic", lambda: next(clock))
    client = SimpleNamespace(
        fonts=lambda: [], run=lambda *a, **k: SimpleNamespace(value=True)
    )
    report = driver["run_suite"](client, tmp_path, {}, [], {})
    assert (
        not report["ok"] and "slow-operation exceeded the 4 s budget" in report["error"]
    )


def test_driver_when_foreign_probe_fails_then_later_phases_and_no_save_cleanup_run(
    driver, tmp_path, monkeypatch
):
    phases = [("lib-foreign-probes", ""), ("later-phase", "")]
    monkeypatch.setitem(driver["run_suite"].__globals__, "phases", lambda: iter(phases))
    events = []

    class Client:
        def fonts(self):
            return [] if not events else [{"id": 42}]

        def close_font(self, **kwargs):
            assert kwargs == {"font_id": 42, "save": False}
            events.append("closed-without-save")
            self.fonts = lambda: []

        def run(self, code, **kwargs):
            name = kwargs.get("phase_name")
            events.append(name)
            value = (
                {"exact": False, "mismatches": ["foreign"]}
                if name == "lib-foreign-probes"
                else True
            )
            return SimpleNamespace(value=value)

    report = driver["run_suite"](Client(), tmp_path, {}, [], {})
    assert "later-phase" in events and "closed-without-save" in events
    assert (
        not report["ok"]
        and report["acceptance_failures"]
        and not report["cleanup_errors"]
    )


@pytest.mark.parametrize("nested", [{"valid": 1.0}, None])
def test_driver_when_vfj_drops_foreign_values_then_delete_and_nested_probe_record(
    driver, nested
):
    from copy import deepcopy

    lib = {
        "fontport.probe.nested": nested,
        "org.fontlab.fontport.acceptance": {"text": "owned"},
    }
    state = {
        "font": SimpleNamespace(lib=lib),
        "backend": SimpleNamespace(get_lib=lambda: deepcopy(lib)),
        "lib_before": {
            "foreign": None,
            "fontport.probe.nested": {"null": None, "valid": 1},
        },
        "foreign": {"fontport.probe.nested": {"null": None, "valid": 1}},
    }
    codes = dict(driver["phases"]())
    exec(compile(codes["lib-comparison-setup"], "comparison", "exec"), state)
    for phase in ("lib-delete", "lib-nested-foreign-edit"):
        exec(compile(codes[phase], phase, "exec"), state)
        assert state["result"]["exact"] is False, phase
        assert state["result"]["mismatches"], phase


def test_driver_when_structured_features_then_all_edit_undo_and_persistence_phases(
    driver, native_features, monkeypatch, tmp_path
):
    from copy import deepcopy

    from feature_steps import feature_phases

    from fontlab_fontport.live import RFont

    backend, data, _, package = native_features
    package.currentHistoryState = lambda: 0
    font = RFont(backend)
    state = {
        "backend": backend,
        "font": font,
        "deepcopy": deepcopy,
        "Path": Path,
        "output": str(tmp_path),
    }

    def save(path):
        Path(path).write_text(json.dumps(data))

    def reopen(path):
        snapshot = json.loads(Path(path).read_text())
        data.clear()
        data.update(snapshot)
        return font

    def action(name):
        key = "feature_rows_before" if name == "actionUndo" else "feature_rows_after"
        data["openTypeFeatures"] = deepcopy(state[key])

    monkeypatch.setattr(font, "save", save)
    monkeypatch.setattr(font, "close", lambda: None)
    state.update(environment=SimpleNamespace(OpenFont=reopen), action=action)
    receipts = {}
    for name, code in feature_phases():
        exec(compile(code, name, "exec"), state)
        receipts[name] = state.pop("result", None)
    assert receipts["feature-baseline"]["supported"] is True
    assert receipts["feature-synthesis-refusal"]["implicit_languagesystem_refused"]
    assert receipts["feature-synthesis-refusal"]["no_history_for_synthesis_refusal"]
    for phase in (
        "feature-readback",
        "feature-undo-readback",
        "feature-redo-readback",
        "feature-reopen-readback",
        "feature-restore-readback",
    ):
        assert (
            receipts[phase]["rows_equal"]
            and receipts[phase]["classes_equal"]
            and receipts[phase]["whole_text_equal"]
        )
    assert data["openTypeFeatures"] == state["feature_rows_before"]


@pytest.mark.parametrize("mismatch", ["boundaries", "text", "classes"])
def test_driver_when_feature_mismatch_then_retains_observed_receipt_and_continues(
    driver, native_features, monkeypatch, tmp_path, mismatch
):
    from copy import deepcopy
    from hashlib import sha256

    from feature_steps import feature_phases

    backend, data, _, _ = native_features
    state = {"backend": backend, "deepcopy": deepcopy}
    exec(compile(dict(feature_phases())["feature-baseline"], "baseline", "exec"), state)
    expected = deepcopy(data["openTypeFeatures"])
    if mismatch == "boundaries":
        data["openTypeFeatures"][1]["name"] = "xxxx"
    elif mismatch == "text":
        data["openTypeFeatures"][1]["feature"] += "# observed change\r\n"
    else:
        data["classes"].clear()
    receipt = state["feature_receipt"](data, expected)
    assert receipt["rows_equal"] is (mismatch == "classes")
    assert receipt["whole_text_equal"] is (mismatch != "text")
    assert receipt["classes_equal"] is (mismatch != "classes")
    assert receipt["openTypeFeatures"] == data["openTypeFeatures"]
    assert receipt["classes"] == data["classes"]
    assert receipt["whole_text"] == "".join(
        row["feature"] for row in data["openTypeFeatures"]
    )
    assert (
        receipt["sha256"]
        == sha256(
            json.dumps(
                data["openTypeFeatures"], ensure_ascii=False, sort_keys=True
            ).encode("utf-8")
        ).hexdigest()
    )
    assert (
        receipt["whole_text_sha256"]
        == sha256(receipt["whole_text"].encode("utf-8")).hexdigest()
    )
    assert (
        receipt["classes_sha256"]
        == sha256(
            json.dumps(data["classes"], ensure_ascii=False, sort_keys=True).encode(
                "utf-8"
            )
        ).hexdigest()
    )
    monkeypatch.setitem(
        driver["run_suite"].__globals__,
        "phases",
        lambda: iter([("feature-undo-readback", ""), ("later", "")]),
    )
    events = []

    def run(code, **kwargs):
        name = kwargs.get("phase_name")
        events.append(name)
        return SimpleNamespace(
            value=receipt if name == "feature-undo-readback" else None
        )

    report = driver["run_suite"](
        SimpleNamespace(fonts=lambda: [], run=run), tmp_path, {}, [], {}
    )
    assert not report["ok"] and "error" not in report and "later" in events
    assert report["phases"][0]["result"] == receipt
    assert report["acceptance_failures"] == [
        {"name": "feature-undo-readback", "result": receipt}
    ]


@pytest.mark.parametrize(
    "failure",
    [
        "noop-history",
        "noop-error",
        "refusal-history",
        "accepted",
        "wrong-capability",
        "wrong-error",
    ],
)
def test_driver_when_feature_noop_or_refusal_fails_then_returns_flags_and_continues(
    driver, native_features, monkeypatch, tmp_path, failure
):
    from feature_steps import feature_phases

    from fontlab_fontport.errors import UnsupportedCapability

    backend, _, _, package = native_features
    states = iter([10, 11] if failure.endswith("history") else [10, 10])
    package.currentHistoryState = lambda: next(states)

    def set_features(text):
        if failure == "wrong-error":
            raise RuntimeError("unexpected failure with diagnostic")
        if failure != "accepted":
            raise UnsupportedCapability(
                "wrong"
                if failure == "wrong-capability"
                else "font.features.text.split",
                "probe",
            )

    monkeypatch.setattr(backend, "set_features", set_features)

    def set_blocks(value):
        if failure == "noop-error":
            raise ValueError("no-op unexpectedly failed")

    phase = "feature-noop" if failure.startswith("noop-") else "feature-split-refusal"
    state = {
        "backend": backend,
        "font": SimpleNamespace(features=SimpleNamespace(set_blocks=set_blocks)),
        "feature_blocks_before": {},
        "UnsupportedCapability": UnsupportedCapability,
    }
    exec(compile(dict(feature_phases())[phase], phase, "exec"), state)
    receipt = state["result"]
    flag = (
        "no_history_for_identical_blocks"
        if failure == "noop-history"
        else "identical_write_succeeded"
        if failure == "noop-error"
        else "no_history_for_split_refusal"
        if failure == "refusal-history"
        else "only_arbitrary_split_refused"
    )
    assert receipt[flag] is False, receipt
    if failure.endswith("history"):
        assert receipt["history_before"] == 10 and receipt["history_after"] == 11
    if failure == "wrong-error":
        assert receipt["refusal"]["message"] == "unexpected failure with diagnostic"
    if failure == "noop-error":
        assert receipt["write_error"]["message"] == "no-op unexpectedly failed"
    monkeypatch.setitem(
        driver["run_suite"].__globals__,
        "phases",
        lambda: iter([(phase, ""), ("later", "")]),
    )
    events = []

    def run(code, **kwargs):
        events.append(kwargs.get("phase_name"))
        return SimpleNamespace(
            value=receipt if kwargs.get("phase_name") == phase else None
        )

    report = driver["run_suite"](
        SimpleNamespace(fonts=lambda: [], run=run), tmp_path, {}, [], {}
    )
    assert not report["ok"] and "error" not in report and "later" in events
    assert report["acceptance_failures"] == [{"name": phase, "result": receipt}]


@pytest.mark.parametrize(
    "phase", ["lib-delete", "lib-nested-foreign-edit", "feature-baseline"]
)
def test_driver_when_post_vfj_or_feature_capability_fails_then_continues_and_marks_failure(
    driver, tmp_path, monkeypatch, phase
):
    monkeypatch.setitem(
        driver["run_suite"].__globals__,
        "phases",
        lambda: iter([(phase, ""), ("later", "")]),
    )
    events = []

    def run(code, **kwargs):
        name = kwargs.get("phase_name")
        events.append(name)
        value = (
            {"supported": False} if phase == "feature-baseline" else {"exact": False}
        )
        return SimpleNamespace(value=value if name == phase else None)

    client = SimpleNamespace(fonts=lambda: [], run=run)
    report = driver["run_suite"](client, tmp_path, {}, [], {})
    assert "later" in events and not report["ok"] and not report["cleanup_errors"]
    assert report["acceptance_failures"][0]["name"] == phase


@pytest.mark.parametrize("value", [None, True, {}, [], {"supported": True}])
def test_driver_when_feature_receipt_shape_changes_then_supported_check_does_not_abort(
    driver, tmp_path, monkeypatch, value
):
    monkeypatch.setitem(
        driver["run_suite"].__globals__,
        "phases",
        lambda: iter([("feature-baseline", "")]),
    )
    client = SimpleNamespace(
        fonts=lambda: [], run=lambda *a, **k: SimpleNamespace(value=value)
    )
    report = driver["run_suite"](client, tmp_path, {}, [], {})
    assert report["ok"], report


def test_driver_when_features_only_then_no_lib_or_ui_phases_and_isolated_timing(driver):
    names = [name for name, code in driver["phases"](features_only=True)]
    assert (
        "feature-restore-readback" in names and "feature-plum-metadata-timing" in names
    )
    assert not any(
        name.startswith(("lib-", "info-", "vanilla-", "batch-")) for name in names
    )


def test_driver_when_only_empty_named_slots_then_baseline_and_stage_record_flags(
    driver, native_features
):
    from copy import deepcopy

    from feature_steps import feature_phases

    backend, data, _, _ = native_features
    data["openTypeFeatures"] = [{"name": "ccmp"}]
    state = {"backend": backend, "deepcopy": deepcopy}
    phases = dict(feature_phases())
    exec(compile(phases["feature-baseline"], "baseline", "exec"), state)
    assert state["result"]["has_named_features"] is False
    assert state["result"]["openTypeFeatures"] == [{"name": "ccmp"}]
    receipt = state["feature_receipt"](data, [{"name": "ccmp"}])
    assert receipt["rows_equal"] and receipt["whole_text_equal"]
    assert receipt["whole_text"] == ""
    exec(compile(phases["feature-stage"], "stage", "exec"), state)
    assert state["result"]["edit_available"] is False


def _fake_root(tmp_path, with_glyport):
    root = tmp_path / "fontport"
    package = root / "src/fontlab_fontport"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("")
    if with_glyport:
        glyport = root / "gp/fontlab_glyport"
        glyport.mkdir(parents=True)
        (glyport / "__init__.py").write_text("")
    return root


def test_arguments_when_glyport_absent_then_origins_cover_fontport_only(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tests" / "native_drivers"))
    from driver_args import arguments

    root = _fake_root(tmp_path, with_glyport=False)
    args = arguments(root, ["--dry-run"])
    assert list(args.origins) == ["fontlab_fontport"], "Glyport is optional unless asked for"
    assert args.glyport is None and args.glyport_required is False, "a skipped check is recorded"


def test_arguments_when_glyport_required_and_absent_then_error(tmp_path, monkeypatch, capsys):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tests" / "native_drivers"))
    from driver_args import arguments

    root = _fake_root(tmp_path, with_glyport=False)
    with pytest.raises(SystemExit):
        arguments(root, ["--require-glyport"])
    assert "fontlab_glyport" in capsys.readouterr().err


def test_arguments_when_glyport_present_then_its_origin_is_recorded(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "tests" / "native_drivers"))
    from driver_args import arguments

    root = _fake_root(tmp_path, with_glyport=True)
    args = arguments(root, ["--extra-source", str(root / "gp"), "--require-glyport"])
    assert set(args.origins) == {"fontlab_fontport", "fontlab_glyport"}
    assert args.glyport == args.origins["fontlab_glyport"] and args.glyport_required is True


def test_driver_when_glyport_skipped_then_dry_run_and_result_json_record_it(driver, tmp_path, monkeypatch, capsys):
    """Both receipts carry glyport=None and glyport_required, never a silently missing key."""
    root = _fake_root(tmp_path, with_glyport=False)
    main = driver["main"]
    glob = main.__globals__
    monkeypatch.setitem(glob, "arguments", lambda _root: _args_for(root, tmp_path))
    assert main() == 0
    dry = json.loads(capsys.readouterr().out)
    assert dry["glyport"] is None and dry["glyport_required"] is False
    assert "fontlab_glyport" not in dry["origins"]

    args = _args_for(root, tmp_path, dry_run=False)
    monkeypatch.setitem(glob, "arguments", lambda _root: args)
    monkeypatch.setitem(glob, "prepare", lambda *_: (tmp_path, [], {}))
    monkeypatch.setitem(glob, "run_suite", lambda *_a, **_k: {"ok": True})
    monkeypatch.setitem(sys.modules, "fontlab_remopy", SimpleNamespace(FontLab=_NullClient))
    assert main() == 0
    result = json.loads((tmp_path / "result.json").read_text())
    assert result["glyport"] is None and result["glyport_required"] is False


class _NullClient:
    def __init__(self, **_kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


def _args_for(root, tmp_path, dry_run=True):
    monkey_path = str(Path(__file__).resolve().parents[1] / "tests" / "native_drivers")
    if monkey_path not in sys.path:
        sys.path.insert(0, monkey_path)
    from driver_args import arguments

    args = arguments(root, ["--dry-run"] if dry_run else [])
    args.dry_run = dry_run
    return args
