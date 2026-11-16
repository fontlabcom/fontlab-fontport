# this_file: tests/test_round10_driver.py
"""Compile native phases and exercise the controller without loading Remopy."""

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def driver(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "tests" / "native_drivers"))
    return importlib.import_module("round10")


def test_driver_arguments_and_every_phase_compile_without_native_contact(
    driver, capsys
):
    assert driver.main(["--suite", "upstream", "--list-tests"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert len(result["test_ids"]) == 1797 and not result["native_contacted"]
    for suite in ("glyph", "world", "interchange", "pens", "boundaries", "lifecycle"):
        assert driver.main(["--suite", suite, "--dry-run"]) == 0
        assert json.loads(capsys.readouterr().out)["suite"] == suite
    phase_sets = [
        driver.glyph_phases(),
        driver.world_phases(["01_metrics"]),
        driver.pen_phases(["A"]),
        driver.boundary_phases(),
        driver.lifecycle_phases(),
        driver.import_phases(Path("/tmp/owned.ufo")),
        driver.compare_phases(["A"], "compare"),
    ]
    for phases in phase_sets:
        for name, code in phases:
            compile(code, name, "exec")
    for code in (driver.WIRE, driver.SETUP, driver.next_step(), driver.start()):
        compile(code, "native-wire", "exec")


def test_phase_mismatch_is_retained_in_jsonl(driver, tmp_path):
    reply = {"equal": False, "observed": [1], "expected": [2]}
    client = SimpleNamespace(run=lambda *args, **kwargs: SimpleNamespace(value=reply))
    run = driver.Run(client, tmp_path, [])
    assert run.step("mismatch", "result={}") == reply
    assert run.failures[0]["result"] == reply
    assert json.loads(run.receipts.read_text())["result"]["observed"] == [1]


def test_upstream_driver_runs_one_id_and_cleanup_in_distinct_calls(driver):
    class FakeRun:
        def __init__(self):
            self.calls = []

        def step(self, name, code):
            self.calls.append((name, code))
            return {"remaining": 0}

    run = FakeRun()
    driver.run_upstream(run, ["test.id1", "test.id2"])
    assert [name for name, _ in run.calls] == [
        "upstream-setup",
        "test.id1",
        "upstream-cleanup",
        "test.id2",
        "upstream-cleanup",
    ]


def test_controller_finally_closes_only_its_owned_ids_after_rpc_failure(
    driver, tmp_path
):
    source = tmp_path / "source.vfj"
    source.write_text("{}")
    output = tmp_path / "output"
    output.mkdir()
    args = driver.arguments(["--suite", "glyph", "--fixture", str(source)])

    class Client:
        def __init__(self):
            self.closed = []
            self.polls = 0

        def fonts(self):
            self.polls += 1
            return [] if self.polls == 1 else [{"id": 42}, {"id": 99}]

        def run(self, *args_, **kwargs):
            phase = kwargs["phase"]
            if phase.startswith("warm-"):
                value = {"file": args.origin}
            elif phase == "owned-ids":
                value = [42]
            elif phase.startswith("owned-create-"):
                raise RuntimeError("injected RPC failure")
            else:
                value = {}
            return SimpleNamespace(value=value)

        def close_font(self, **kwargs):
            self.closed.append(kwargs)

    client = Client()
    run = driver.execute(client, args, output, [])
    assert client.closed == [{"font_id": 42, "save": False}]
    assert run.failures and "injected RPC failure" in run.failures[0]["terminal_error"]
    assert source.read_text() == "{}"


def test_save_refusal_skips_close_and_reopen(driver, tmp_path):
    class Client:
        def __init__(self):
            self.calls = []

        def run(self, wire, **kwargs):
            self.calls.append((kwargs["phase"], kwargs["code"]))
            return SimpleNamespace(
                value={"status": "UnsupportedCapability"}
                if kwargs["phase"] == "probe-save"
                else {}
            )

    client = Client()
    run = driver.Run(client, tmp_path, [])
    run.phases(
        [
            ("probe-save", "font.save(path)"),
            ("probe-close", "font.close()"),
            ("probe-reopen", "font=environment.OpenFont(path)"),
            ("probe-reopen-read", "result=font.keys()"),
        ]
    )
    assert all(
        "skipped" in code
        for name, code in client.calls
        if name in ("probe-close", "probe-reopen", "probe-reopen-read")
    )


def test_reopen_failure_stops_dependent_suite(driver, tmp_path):
    client = SimpleNamespace(
        run=lambda *a, **k: SimpleNamespace(value={"phase_error": "missing file"})
    )
    run = driver.Run(client, tmp_path, [])
    with pytest.raises(RuntimeError, match="Reopen failed"):
        run.step("probe-reopen", "font=environment.OpenFont(path)")
    assert run.failures and "missing file" in run.receipts.read_text()


@pytest.mark.parametrize("depth", ["fontlab-fontport", ".worktrees/issue-105-fontport"])
def test_wrapper_finds_workspace_at_both_checkout_depths(tmp_path, depth):
    import os
    import shutil
    import subprocess

    root = Path(__file__).resolve().parents[1]
    checkout = tmp_path / depth
    drivers = checkout / "tests" / "native_drivers"
    drivers.mkdir(parents=True)
    shutil.copy2(root / "tests/native_drivers/run-round10.sh", drivers)
    marker = tmp_path / "verification/issue-104/fl-native.sh"
    marker.parent.mkdir(parents=True)
    marker.write_text("exit 99\n")  # Dry run must never invoke native session wrapper.
    executable = tmp_path / "bin/uv"
    executable.parent.mkdir()
    executable.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
    executable.chmod(0o755)
    reply = subprocess.run(
        ["sh", str(drivers / "run-round10.sh"), "--suite", "upstream", "--dry-run"],
        env={
            **os.environ,
            "PATH": str(executable.parent) + os.pathsep + os.environ["PATH"],
        },
        text=True,
        capture_output=True,
        check=True,
    )
    args = reply.stdout.splitlines()
    assert args[args.index("--project") + 1] == str(checkout)
    assert args[args.index("--workspace") + 1] == str(tmp_path)


def test_hinted_phases_compile_and_bounds_tolerance(driver):
    from round10_glyph_steps import hinted_phases
    from round10_pen_steps import bounds_equal

    for name, code in hinted_phases(["A", "V"]):
        compile(code, name, "exec")
    assert bounds_equal((0, -100, 500, 800), (0.0000001, -100, 500, 800))
    assert not bounds_equal((0, -100, 500, 800), (0, 800, 500, -100))
    assert not bounds_equal((0, 0, 1, 1), (0, 0, 1.1, 1))
    assert bounds_equal(None, None) and not bounds_equal(None, (0, 0, 0, 0))


def test_world_examples_receive_owned_fixture_even_without_an_active_document(
    driver, tmp_path, monkeypatch
):
    from round10_world_steps import phases

    from fontlab_fontport.live import RFont
    from fontlab_fontport.memory import UFOBackend

    source = tmp_path / "ownership_probe.py"
    source.write_text(
        'def run(font):\n    return {"ok": font._backend.owns_document}\n'
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    backend = UFOBackend()
    backend.owns_document = True
    font = RFont(backend)
    code = dict(phases(["ownership_probe"]))["example-ownership_probe"]
    state = {"font": font}
    exec(code, state)
    assert state["result"] == {"ok": True}
    font.close()


def test_world_unexpected_example_refusal_is_a_failure(driver, tmp_path):
    reply = {"status": "UnsupportedCapability", "capability": "examples.ownership"}
    client = SimpleNamespace(run=lambda *a, **k: SimpleNamespace(value=reply))
    run = driver.Run(client, tmp_path, [])
    run.step("example-probe", "result={}")
    assert run.failures[0]["result"] == reply


def test_hint_candidate_phase_uses_real_backend_method_and_checks_reply_type(driver):
    import inspect

    code = inspect.getsource(driver.execute)
    assert "backend.glyph_names(backend.default_layer())" in code
    assert "if not isinstance(names, list)" in code
    assert "backend.keys(" not in code


def test_native_bounds_oracle_uses_control_points(driver):
    from fontParts.fontshell import RGlyph
    from fontTools.pens.boundsPen import ControlBoundsPen

    from fontlab_fontport.recipes import bounds, control_bounds

    glyph = RGlyph()
    pen = glyph.getPen()
    pen.moveTo((0, 0))
    pen.curveTo((10, 100), (90, 100), (100, 0))
    pen.endPath()
    oracle = ControlBoundsPen(None)
    glyph.draw(oracle)
    assert control_bounds(glyph) == oracle.bounds == (0, 0, 100, 100)
    assert bounds(glyph)[3] == 75
    code = dict(driver.pen_phases(["A"]))["pens-A"]
    assert "bounds_equal(control_bounds(g,font),native_bounds)" in code


def test_supported_edit_receipt_does_not_claim_expected_refusal(driver):
    import ast

    from round10_common_steps import SETUP

    from fontlab_fontport.errors import UnsupportedCapability

    definition = next(
        node
        for node in ast.parse(SETUP).body
        if isinstance(node, ast.FunctionDef) and node.name == "edit_receipt"
    )
    state = {
        "UnsupportedCapability": UnsupportedCapability,
        "history": lambda name=None: 1,
        "probe_name": "A",
        "glyph_history": lambda backend, name: {"index": 1, "rows": [1], "objects": []},
        "history_before": 0,
        "history_rows_before": 0,
        "backend": SimpleNamespace(
            _package=lambda: SimpleNamespace(historyStates=lambda accepted: ["one"])
        ),
    }
    exec(
        compile(ast.Module(body=[definition], type_ignores=[]), "<receipt>", "exec"),
        state,
    )
    supported = state["edit_receipt"]("pass")
    assert supported["expected_refusal"] is None
    assert supported["capability_matches_expectation"] and supported["one_history_row"]
    refused = state["edit_receipt"](
        "raise UnsupportedCapability('test.limit','limit')",
        expected_capability="test.limit",
    )
    assert (
        refused["expected_refusal"] == "test.limit"
        and refused["capability_matches_expectation"]
    )
    unexpected = state["edit_receipt"](
        "raise UnsupportedCapability('test.limit','limit')"
    )
    assert not unexpected["capability_matches_expectation"]
