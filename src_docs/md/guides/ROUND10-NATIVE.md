---
this_file: src_docs/md/guides/ROUND10-NATIVE.md
---

# Round 10 handoff to C4

Current corrections and re-run observations: [Round 12](ROUND12-NATIVE.md).

This implementation was developed without FontLab or Remopy. Native timings,
payloads, exact Undo rows and VFJ persistence are **not verified** here. Keep
issues/105 rows 27/30/31 open until C4 has the receipts required by GAPS.md.

From this worktree, C4 runs each command separately in a fresh dedicated session:

```sh
sh tests/native_drivers/run-round10.sh --suite upstream
sh tests/native_drivers/run-round10.sh --suite glyph
sh tests/native_drivers/run-round10.sh --suite world
sh tests/native_drivers/run-round10.sh --suite interchange
sh tests/native_drivers/run-round10.sh --suite pens
sh tests/native_drivers/run-round10.sh --suite boundaries
sh tests/native_drivers/run-round10.sh --suite lifecycle
```

The wrapper uses `verification/issue-104/fl-native.sh --mutating --lane C4`.
It resolves this checkout and workspace, then runs the controller with the
checkout project environment, with the local Remopy project added for native execution.
Offline --dry-run uses the same checkout plus Remopy dependency environment and bypasses the host wrapper. Restart FontLab after each
mutating command, including failures. The controller requires no open documents,
purges stale Fontport/driver modules before warming, puts its own src first and
checks `__file__`. Output goes to unique ignored `.local/round10/<UTC>-<uuid>/`.
It copies the corpus before opening, hashes the original, tracks only owned IDs,
and closes those IDs with `close_font(save=False)` in finally. No user documents,
Qt application, timers, or deferred-delete flushes are used.

For variable and non-Latin checks repeat the commands with an **absolute**
`--fixture /.../getgo/.../font.vfj`. Use `cc0/plum/plum-var.vfj` for variable
axes, `cc0/medi/medi.vfj` for Latin and `apache/zotosans/zotosans-georgian.vfj`
for non-Latin interchange (one master, 127 source glyphs, two feature rows).
The latter does not need A/V; the example/pens/geometry suites do. All suites
default to Medio. Artifacts: repeat `--source /absolute/installed/site-packages`
(for independent wheel and sdist installs); checkout src must be excluded for
those runs. `--source` is repeatable for actual dependency roots.

Exact extra fixture commands, still one command per restarted native session:

```sh
FONTPORT_WORKSPACE="$PWD"
while [ ! -f "$FONTPORT_WORKSPACE/verification/issue-104/fl-native.sh" ]; do
    [ "$FONTPORT_WORKSPACE" != / ] || exit 2
    FONTPORT_WORKSPACE=$(dirname "$FONTPORT_WORKSPACE")
done
FONTPORT_GETGO="$FONTPORT_WORKSPACE/fontlab-python-examples/testdata/getgo"
sh tests/native_drivers/run-round10.sh --suite glyph --fixture "$FONTPORT_GETGO/cc0/plum/plum-var.vfj"
sh tests/native_drivers/run-round10.sh --suite pens --fixture "$FONTPORT_GETGO/cc0/plum/plum-var.vfj"
sh tests/native_drivers/run-round10.sh --suite interchange --fixture "$FONTPORT_GETGO/cc0/plum/plum-var.vfj"
sh tests/native_drivers/run-round10.sh --suite interchange --fixture "$FONTPORT_GETGO/apache/zotosans/zotosans-georgian.vfj"
```

Offline controller checks (safe in this host-free lane):

```sh
uv run python tests/native_drivers/round10.py --suite upstream --list-tests
uv run python tests/native_drivers/round10.py --suite glyph --dry-run
sh -n tests/native_drivers/run-round10.sh
```

Each phase has a three-second Python trace guard and a measured four-second RPC
gate. The upstream suite additionally checks a 2.5-second Python budget. Warm
imports, open, edit, snapshots, Undo, Redo, save, close and reopen are separate
calls. Export/import advance one glyph or metadata unit per call; bulk UFO disk
serialization runs in the client. Native C++ calls cannot be interrupted by a
Python trace guard. A slow C++ call is a **failed timing gate**, never evidence
that an arbitrary call is preemptible. C4 must return its phase/timing as a
ticket. The controller polls the host between feature phases. It schedules no
background work that could outlive its lock.

`receipts.jsonl` keeps every result, expected/observed payload, equality flag,
exception and timing. Each upstream ID has one result line plus separate cleanup
lines. A mismatch or unknown failure causes exit 1 and remains in `result.json`.
Known named capability refusals are records, not aborts. No assertion prevents
an observation being written. Unknown native failures require C4 classification
and an fl issue; no issue number or native pass is fabricated by this lane.

| Brief item | Code and phases | Acceptance / remaining limit |
|---|---|---|
| 1 / 30.1 | testing.py; upstream_steps.py; `--suite upstream`; FONTPARTS-COVERAGE.md | 1,797 IDs; explicit native orphan contract; attached native fixtures attempted separately. Guideline/image fixtures refuse. Native classification pending |
| 2 / 30.2 | FONTPARTS-COVERAGE.md introduction + per-ID ledger | Full RoboFab checklist mapping; distinguish a passing deprecated dispatch test from native cache-update proof |
| 3 / 27.1 | live.edit_glyph; host.write_glyph_named; round10_glyph_steps.py | One backend write/notification for staged geometry; exact native first Undo/row count still needs C4. Unsupported topology/component replacement/guides/hinted/shared writes refuse. Unicode names now refuse before create/write |
| 4 / 27.6 | world.register/unregister; deploy.write_launcher; 19 examples; round10_world_steps.py | Persistent/context registration restore real callbacks; launcher only writes its explicit path; CurrentGlyph/selection named refusal. New/Open/current/all callbacks and all scripts get native receipts |
| 5 / 27.4 | interchange.py; round10_interchange_steps.py | Full supported UFO model round-trip host-free; incremental native export, strict single-layer native import, compare and VFJ reopen. Loss inventory in UFO-INTERCHANGE.md. Multilayer native import refuses before allocation |
| 6 / 27.2–3 | recipes.py; round10_pen_steps.py | Per-glyph digest vs the same export read path, native rectangle vs BoundsPen; flatten Undo/Redo; Designspace native axes/master receipts; feaLib parse with native classes. Native all-GetGo execution pending |
| 7 / 30.3 | capabilities.NATIVE_CAPABILITIES | `glyph.externalChangeNotifications.supported == False`; App can show “Reload required”. No automatic dirty/representation coherence is claimed |
| 8 / 30.4 | host._stage_source; native_kerning; glyph/fractional-anchor and boundary/fractional-kerning phases | Exact named refusals before native writes/history; host-free rollback/preflight tested |
| 9 / 31.6 / 31.1 | capabilities.STRUCTURED_ROUTES; round10_boundary_steps.py | Master-backed Panose/weight/width routes; changing name-record writes refuse explicitly (Round 12). D18 default info/save remains editable; strict refusals are opt-in. Owned both-sided/legacy fixtures are created in separate setup phases; see NATIVE-BOUNDARIES.md |
| 10 / 27.7 | errors.StaleObjectError; lifetime.py; live_objects.py; round10_lifecycle_steps.py | Cached glyph/point/lib/info/layer reads check owner lifetime. External owned close + explicit VFJ save/reopen phases. Native proof pending |

The native geometry suite retains complete target glyph payloads (including
other layers/hints) through first Undo/Redo and reopen. C4 must review the
edit-to-baseline diff and count/name the native Undo rows; an RPC notification
count is not a native Undo-row proof. Source only confirms the two-string
component constructor in `Proteus/pygate/pyflshape.cpp:65–79`; it is missing from
the captured flShape constructor list, so this particular mandatory two-argument
overload stays positional. Optional native overload arguments remain keywords.

The Ω guard follows C4's measured `Ω → Î©` kerning-source2 VFJ result. Inspected
`flglyph.cpp:2768,3043` writes UTF-8 binary tags, which does not isolate the VFJ
bug. We therefore refuse non-ASCII native glyph creation/rename/geometry writes,
component references, and saves of documents already containing such names
rather than applying a speculative double-encoding conversion. Existing fonts
are read as stored; this does not repair already-corrupted names.

## Round 11 receipt corrections

Run upstream twice in separate fresh sessions: the command above records orphan
fixtures; `sh tests/native_drivers/run-round10.sh --suite upstream --native-attached`
records owned attached fixtures. The ledger keeps both native columns pending
until C4 runs them. Each run resets fixture attribution per test, caches the ID
map once and warms fontParts.test in a separate call. Parent assertion failures
in attached mode stay unclassified; bare NotImplementedError is never a capability.

The glyph suite scans one glyph per call for hints. Choose a hinted GetGo fixture
with --fixture; missing hints are an explicit failed prerequisite, not proof.
The hinted write must refuse exactly glyph.geometry with unchanged payload/history.
Supported glyph/flatten operations record one_history_row against historyStates.
Bounds comparison keeps the native y convention and tolerates only 1e-6-unit
numeric extrema drift (relative tolerance 1e-9), retaining both raw bounds.
Undo/Redo activates the owned font first (mcptools.cpp:309–314 set_active_font).
Save refusal skips close/reopen; reopen failure aborts dependent suite work.
Retained raw native fixture references are released before final document close.

The deploy launcher is a startup script; never push its cold imports through
run_python. Restart FontLab before suites to avoid already-loaded third-party
package versions; warm-phase receipts include module origins.
