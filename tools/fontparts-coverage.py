# this_file: tools/fontparts-coverage.py
"""Regenerate host-free parity and import C4 observed native per-ID receipts."""

import argparse
import json
import re
from collections import Counter
from importlib.metadata import version
from pathlib import Path

from fontlab_fontport.memory import UFOBackend
from fontlab_fontport.testing import ObjectGenerator, run_test, upstream_tests

ROOT = Path(__file__).resolve().parents[1]


def native_status(row):
    """Use C4 classifications; never infer pass from an aggregate count."""
    status = row["status"]
    if status == "pass":
        return "pass"
    if status not in ("UnsupportedCapability", "HarnessExclusion"):
        raise ValueError(f"Unclassified native ID {row['id']}: {status}")
    names = (
        [row["capability"]]
        if row.get("capability")
        else re.findall(
            r"^fontlab_fontport.errors.UnsupportedCapability: ([^\s:]+):",
            "\n".join(row.get("errors", [])),
            re.MULTILINE,
        )
    )
    if not names:
        raise ValueError(f"Native ID {row['id']} has no named {status}")
    label = "capability" if status == "UnsupportedCapability" else "harness exclusion"
    return label + ": " + "; ".join(dict.fromkeys(names))


def load_native(directory, expected_ids):
    """Require one complete observed run and reconcile its aggregate result."""
    paths = list(directory.glob("*/receipts.jsonl"))
    if len(paths) != 1:
        raise ValueError(f"Expected exactly one native run in {directory}: {paths}")
    path = paths[0]
    result = json.loads(path.with_name("result.json").read_text())
    rows, counts = {}, Counter()
    for line in path.read_text().splitlines():
        row = json.loads(line).get("result")
        if not isinstance(row, dict) or "id" not in row or "status" not in row:
            continue
        if row["id"] in rows:
            raise ValueError(f"Duplicate native ID: {row['id']}")
        rows[row["id"]] = native_status(row)
        counts[row["status"]] += 1
    if set(rows) != expected_ids:
        raise ValueError(
            f"Native ID mismatch: missing={expected_ids - set(rows)}, extra={set(rows) - expected_ids}"
        )
    if (
        not result.get("ok")
        or result.get("failures")
        or dict(counts) != result["upstream_counts"]
    ):
        raise ValueError(f"Native aggregate disagrees with per-ID receipts: {path}")
    print(directory.name, dict(counts))
    return rows


def evidence_directory():
    for ancestor in ROOT.parents:
        candidate = ancestor / "verification/issue-106/evidence/issue-105/round14"
        if candidate.is_dir():
            return candidate
    raise ValueError(
        "C4 f3d7dc5 evidence not found; supply --native-evidence pointing to round14"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--native-evidence", type=Path, help="C4 f3d7dc5 round14 directory"
    )
    parser.add_argument(
        "--reuse-parity",
        action="store_true",
        help="Read committed host-free parity receipts without replacing historical timings",
    )
    args = parser.parse_args()
    native_root = args.native_evidence or evidence_directory()
    ids = {case.id() for case in upstream_tests()}
    native = {
        "orphan": load_native(native_root / "upstream-out", ids),
        "attached": load_native(native_root / "upstream-attached-out", ids),
    }
    receipts = ROOT / "verification/issue-105/round10"
    receipts.mkdir(parents=True, exist_ok=True)
    surfaces = {}
    for mode in ("fontshell", "memory"):
        if args.reuse_parity:
            rows = [
                json.loads(line)
                for line in (receipts / (mode + ".jsonl")).read_text().splitlines()
            ]
        else:
            rows = [
                run_test(
                    case,
                    ObjectGenerator(
                        fontshell=mode == "fontshell",
                        backend_factory=UFOBackend if mode == "memory" else None,
                    ),
                )
                for case in upstream_tests()
            ]
            payload = "".join(
                json.dumps(row, ensure_ascii=False) + "\n" for row in rows
            )
            (receipts / (mode + ".jsonl")).write_text(
                payload.replace(str(ROOT), "<checkout>")
            )
        if {row["id"] for row in rows} != ids or len(rows) != len(ids):
            raise ValueError(f"Host-free ID mismatch: {mode}")
        surfaces[mode] = rows
        if any(row["status"] == "unclassified" for row in rows):
            raise RuntimeError(
                f"Unclassified host-free failures in {mode}; inspect {receipts / (mode + '.jsonl')}"
            )
        print(mode, dict(Counter(row["status"] for row in rows)))
    preamble = (
        (ROOT / "src_docs/md/guides/FONTPARTS-COVERAGE.md")
        .read_text()
        .split("\n## Per-test ledger", 1)[0].rstrip()
    )
    lines = [
        preamble,
        "\n## Per-test ledger\n",
        "Versions: "
        + ", ".join(
            f"{name} {version(name)}"
            for name in ("fontParts", "defcon", "fontPens", "fontTools", "ufoLib2")
        )
        + ".\n",
        "| Upstream test ID | fontshell parity | Live-font / detached-orphan result | Fixtures actually used | Native orphan C4 | Native attached C4 |",
        "|---|---|---|---|---|---|",
    ]
    for parity, row in zip(surfaces["fontshell"], surfaces["memory"], strict=True):
        status = row["status"]
        if status == "UnsupportedCapability":
            reasons = list(
                dict.fromkeys(
                    error.rstrip().splitlines()[-1] for error in row["errors"]
                )
            )
            status += ": " + "; ".join(reasons)
        elif row["skipped"]:
            status += ": " + "; ".join(row["skipped"])
        routes = (
            ", ".join(
                sorted(
                    {
                        f"{fixture['family']}={fixture['route']}"
                        for fixture in row["fixtures"]
                    }
                )
            )
            or "none"
        )
        lines.append(
            f"| `{row['id']}` | {parity['status']} | {status.replace('|', ' / ')} | {routes} | {native['orphan'][row['id']]} | {native['attached'][row['id']]} |"
        )
    (ROOT / "src_docs/md/guides/FONTPARTS-COVERAGE.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
