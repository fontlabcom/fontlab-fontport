# this_file: tests/test_coverage_tool_docs.py
"""Exercise the coverage-maintenance CLI only in owned synthetic fixture roots.

These tests do not refresh the committed 1797-row ledger or native acceptance.
"""
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def tool():
    path = Path(__file__).parents[1] / "tools/fontparts-coverage.py"
    spec = importlib.util.spec_from_file_location("coverage_tool_docs", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def native_run(directory, rows, **overrides):
    run = directory / "owned-run"
    run.mkdir(parents=True)
    (run / "receipts.jsonl").write_text("{}\n" + "".join(json.dumps({"result": row}) + "\n" for row in rows))
    result = {"ok": True, "failures": [], "upstream_counts": {"pass": len(rows)}}
    result.update(overrides)
    (run / "result.json").write_text(json.dumps(result))
    return run


@pytest.mark.parametrize("fault", ["missing-run", "multiple-runs", "duplicate-id", "missing-id", "not-ok", "failures", "counts"])
def test_native_receipts_when_inconsistent_then_refuse(tool, tmp_path, fault):
    rows = [{"id": "owned.a", "status": "pass"}]
    if fault == "missing-run":
        with pytest.raises(ValueError, match="exactly one"):
            tool.load_native(tmp_path, {"owned.a"})
        return
    if fault == "duplicate-id":
        rows *= 2
    overrides = {"ok": False} if fault == "not-ok" else {"failures": ["owned failure"]} if fault == "failures" else {"upstream_counts": {}} if fault == "counts" else {}
    native_run(tmp_path, rows, **overrides)
    if fault == "multiple-runs":
        another = tmp_path / "another"
        another.mkdir()
        (another / "receipts.jsonl").touch()
    expected = {"owned.other"} if fault == "missing-id" else {"owned.a"}
    with pytest.raises(ValueError):
        tool.load_native(tmp_path, expected)


def test_evidence_lookup_when_bounded_ancestors_supplied_then_resolves_or_refuses(tool, tmp_path, monkeypatch):
    ancestor = tmp_path / "owned-ancestor"
    monkeypatch.setattr(tool, "ROOT", SimpleNamespace(parents=[ancestor]))
    with pytest.raises(ValueError, match="evidence not found"):
        tool.evidence_directory()
    expected = ancestor / "verification/issue-106/evidence/issue-105/round14"
    expected.mkdir(parents=True)
    assert tool.evidence_directory() == expected


@pytest.fixture
def cli_fixture(tool, tmp_path, monkeypatch):
    root = tmp_path / "owned-source"
    document = root / "src_docs/md/guides/FONTPARTS-COVERAGE.md"
    document.parent.mkdir(parents=True)
    document.write_text("# Test-only owned fixture ledger\n\n## Per-test ledger\nold fixture rows\n")
    monkeypatch.setattr(tool, "ROOT", root)
    ids = ["owned.a", "owned.b", "owned.c"]
    cases = [SimpleNamespace(id=lambda name=name: name) for name in ids]
    monkeypatch.setattr(tool, "upstream_tests", lambda: iter(cases))
    native = tmp_path / "synthetic-native-evidence"
    for mode in ["upstream-out", "upstream-attached-out"]:
        native_run(native / mode, [{"id": name, "status": "pass"} for name in ids])
    receipts = root / "verification/issue-105/round10"
    receipts.mkdir(parents=True)
    rows = [
        {"id": ids[0], "status": "pass", "errors": [], "skipped": [], "fixtures": [{"family": "owned", "route": "memory"}]},
        {"id": ids[1], "status": "UnsupportedCapability", "errors": ["Traceback\nOwned | capability", "Traceback\nOwned | capability"], "skipped": [], "fixtures": []},
        {"id": ids[2], "status": "pass", "errors": [], "skipped": ["owned skip reason"], "fixtures": []},
    ]
    for mode in ["fontshell", "memory"]:
        (receipts / (mode + ".jsonl")).write_text("".join(json.dumps(row) + "\n" for row in rows))
    monkeypatch.setattr(sys, "argv", ["coverage-fixture", "--native-evidence", str(native)])
    return tool, root, document, receipts, cases, rows


@pytest.mark.parametrize("reuse", [False, True])
def test_cli_when_authored_guide_moved_then_keeps_fixture_classifications_and_output_boundary(cli_fixture, monkeypatch, reuse):
    tool, root, document, receipts, cases, rows = cli_fixture
    calls = []
    def run_owned_case(case, generator):
        calls.append((case.id(), generator.fontshell))
        return rows[cases.index(case)]
    monkeypatch.setattr(tool, "run_test", run_owned_case)
    if reuse:
        monkeypatch.setattr(sys, "argv", [*sys.argv, "--reuse-parity"])
    before = {p.name: p.read_bytes() for p in receipts.glob("*.jsonl")}
    tool.main()
    text = document.read_text()
    assert text.startswith("# Test-only owned fixture ledger\n")
    assert sum(line.startswith("| `owned.") for line in text.splitlines()) == 3
    assert "UnsupportedCapability: Owned  /  capability" in text
    assert "pass: owned skip reason" in text
    assert "owned=memory" in text
    assert not (root / "docs").exists(), "Maintenance must never rewrite generated website output"
    assert len(calls) == (0 if reuse else 6)
    if reuse:
        assert {p.name: p.read_bytes() for p in receipts.glob("*.jsonl")} == before


@pytest.mark.parametrize("fault", ["wrong-id", "duplicate-id", "unclassified"])
def test_cli_when_hostfree_receipts_invalid_then_refuses_before_writing_guide(cli_fixture, monkeypatch, fault):
    tool, _root, document, receipts, _cases, rows = cli_fixture
    monkeypatch.setattr(sys, "argv", [*sys.argv, "--reuse-parity"])
    bad = [dict(row) for row in rows]
    if fault == "wrong-id":
        bad[0]["id"] = "owned.foreign"
    elif fault == "duplicate-id":
        bad[0]["id"] = bad[1]["id"]
    else:
        bad[0]["status"] = "unclassified"
    (receipts / "fontshell.jsonl").write_text("".join(json.dumps(row) + "\n" for row in bad))
    before = document.read_bytes()
    with pytest.raises((ValueError, RuntimeError)):
        tool.main()
    assert document.read_bytes() == before
