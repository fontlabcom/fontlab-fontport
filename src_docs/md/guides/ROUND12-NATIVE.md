---
this_file: src_docs/md/guides/ROUND12-NATIVE.md
---

# C4 re-run after Fontport T1–T13 repairs

The input is C4's FontLab 9.0.9783 evidence at workspace
verification/issue-106/evidence/issue-105/round10/TICKETS.md. Original receipts
remain untouched. These repairs are host-free and need fresh native proof.

Each command is a separate restarted, no-user-document session. The wrapper
finds the workspace, supplies client dependencies and creates unique owned-copy
outputs. No corpus or user font is written; owned documents close with
close_font(save=False) in finally. Each native phase has a 3-second Python
budget and a 4-second wall-time failure boundary, with polls between phases.

```sh
sh tests/native_drivers/run-round10.sh --suite upstream
sh tests/native_drivers/run-round10.sh --suite upstream --native-attached
sh tests/native_drivers/run-round10.sh --suite glyph
sh tests/native_drivers/run-round10.sh --suite world
sh tests/native_drivers/run-round10.sh --suite interchange
sh tests/native_drivers/run-round10.sh --suite pens
sh tests/native_drivers/run-round10.sh --suite boundaries
sh tests/native_drivers/run-round10.sh --suite lifecycle
```

Append --dry-run to validate wrapper startup without contacting FontLab or
importing Remopy. For T11 use the default owned Medio copy (its exclam and other
glyphs have stored hints), and repeat glyph with an absolute fixture path to
getgo/apache/hint/hint.vfj for TTH. The source VFJs were inspected read-only;
actual target.hasHints/hasTTH detection still needs C4 proof.

| Ticket | Repair / files | Native acceptance |
|---|---|---|
| T1 | native_groups.py, native_kerning.py | Missing native glyph/group references refuse kerning.danglingNames before writes/history. No phantom glyphs are created; plain feature groups retain their existing semantics. |
| T2 | info.py | family/style/OS2 None refuses info.unset; no TypeError/ValueError for these host absence limits. Metric absence keeps its field-specific name. |
| T3 | info.py | 1000.0 stages as integer 1000; non-integral values still fail. Export → import preflight must proceed past UPM. |
| T4 | testing.py, pens.py, live.py | Empty attached contour fixture; open/closed/cubic/quadratic/offcurve edits have no transient PenError. Incomplete point sequences remain pending in Python, never written as invalid contours. Native save refuses glyph.incompleteContours until corrected. Empty contours allocate no native geometry. |
| T5 | host.py | QVariant tuples recursively read as lists. Only com.fontlab.kerningClassesInMainMaster is hidden; raw key survives edits/clear and refuses public writes as lib.reservedKey. Re-run upstream lib keys/length/array tests and existing foreign-value lib phases. |
| T6 | pens.py, live_objects.py, transfer.py | identifiers carries a name; generating an anchor/point/contour/component ID refuses before defcon mutates, preventing the rollback KeyError. All deliberate own-adapter NotImplementedError paths are named capabilities. |
| T7 | live.py, host.py, interchange.py | Missing/cyclic bases refuse components.unresolvedBase before writes/allocation; no poisoned defcon observers. |
| T8 | testing_exclusions.py, testing.py, round10.py | Exact 72 C4-reviewed parent/orphan IDs are HarnessExclusion/testing.nativeAttached.parents only in attached mode. Result upstream_counts separately counts them. Other assertions and bare NotImplementedError remain failures. |
| T9 | host.py, capabilities.py, round10_boundary_steps.py | Panose/weight/width use the actual master properties, with read/edit/Undo/Redo/VFJ comparisons and has_undo_step. Name-record changing writes refuse info.openTypeNameRecords.persistence with unchanged data/history. Stems retain existing routes. |
| T10 | host.py | checkInitHistoryState, then notify(name, [layer, glyph]) before and after a real glyph write; staged flatten follows the same path. Supported edits must produce exactly one history row and Undo must restore the baseline. No-op geometry/metadata skips history. |
| T11 | round10.py, round10_glyph_steps.py | glyph_names instead of nonexistent keys(); verify list-of-strings before iteration, abort malformed reply. Hinted probe always adds real geometry and must refuse glyph.geometry with unchanged payload/history. |
| T12 | recipes.py, round10_pen_steps.py | Native boundingBox compares to ControlBoundsPen; retain exact BoundsPen curve-extrema separately. Numeric tolerance only, no hidden y-axis reversal. |
| T13 | round10_world_steps.py, round10.py | Activate the owned fixture after closing auxiliary documents and pass it to each example.run(font). Ownership remains strict. Unexpected thrown example refusals fail the suite; 19 scripts must actually run, with >=15 real edits. |

## T9 source evidence

Read-only C++ root: `<FontLab C++ source checkout>` (FontLab Ltd. internal, read-only).

- Font Info load/store uses weight_value/width_value and panose_string:
  Proteus/workspace2/fontinfo_data.cpp:391–402,586–596.
- Their Python properties are bound at Proteus/pygate/pyflpackage.cpp:949,951,
  1512–1516. Echopy fontlab.pyi declares weight_value, width_value and panose.
- Master storage setters: Proteus/common/model/flpackage.cpp:17211–17220,
  17350–17360. Master VFJ/history serialization writes the actual weight/width
  fields at :5853–5854 and Panose at :5875; reads at :4855–4860,4921–4925.
- The old info setters write regenerated fg::Style data at
  Proteus/pygate/pyflpackage.cpp:2031–2078,2263–2287,2724–2758.
- Real localized names are stored by Font Info via setLocalizedNames at
  fontinfo_data.cpp:520 and flpackage.cpp:16806–16836. That API has no Python
  binding in pyflpackage.cpp or echopy stubs. MCP's supported global write fields
  (Proteus/common/mcp/mcptools_fonts.cpp:469–565) omit localized/name records.
  Fontport therefore refuses changing name-record batches, including mixed
  batches, before history/data changes. It does not claim native support from
  the existence of the derived fg::Style setter.

T1 resolves actual native references rather than creating placeholders: MCP's
class creation requires glyphListFromNames before commAddKerningGroup
(Proteus/common/mcp/mcptools_metrics_kerning.cpp:709–715).

391 real upstream contour/segment/bPoint/point IDs also run host-free over a
UFO backend that validates every forwarded contour using the actual FontGate
point-pen adapter. This is geometry-contract coverage, not native Undo proof.
