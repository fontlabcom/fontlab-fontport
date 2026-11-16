---
this_file: src_docs/md/guides/ROUND13-NATIVE.md
---

# C4 re-run: Round 13

Input: workspace verification/issue-106/evidence/issue-105/round12/TICKETS.md
(FontLab 9.0.9783, baseline 94b266a). Original native receipts are unchanged.
Host-free regressions exercise the repaired adapters and actual driver wire;
Undo, persistence and timing require fresh C4 receipts.

Run each command in a fresh FontLab session using the shared wrapper's session
policy. It operates on owned copies and closes with save=False in cleanup.

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

Repeat glyph and pens with --fixture followed by the absolute path to the
GetGo plum variable VFJ; repeat interchange with the Georgian VFJ. Medio is the
default fixture. Repeat the hinted refusal probe with the GetGo hint VFJ.
Append --dry-run for offline wrapper validation. Native phases retain the
3-second Python budget and 4-second wall-time gate.

| Ticket | Implementation | C4 acceptance |
|---|---|---|
| T10a | host.py marks shapeData changed after clearContours | Clear, Undo triangle, Redo empty; one history row. |
| T10b | host.py marks component shape changed after transform | Undo restores 10/20, Redo restores 30/40; one row. |
| T14 | round10_history.py visits glyph/layers/shapes/shapeData | Observe their historyStates/currentHistoryState, excluding initial state 0; union accepted row IDs increases by one; Undo/Redo matches payloads. Raw per-object state remains in receipts. |
| T15 | round10_payloads.py | Only a bare empty elementData shape equals absent geometry. Other metadata, hints, transforms and unrelated glyphs remain checked. |
| T16 | recipes.py and round10.py | Rounded FlattenPen digest equals readback; one row, Undo/Redo. Rounding tolerance is <=0.5 per sampled axis; see LIVE-PEN-RECIPES.md. |
| T17 | info.py | Medio exported width IntEnum becomes plain int; import and VFJ reopen pass. Bool remains rejected. |
| T18 | round10_payloads.py | Ignore only per-layer active UI state, named fontlab.layer.activeUIState; retain raw expected/observed payloads. |
| T19 | round10_transfer.py and round10.py | Georgian export/import succeeds without any reply reaching 64 KiB. Large JSON, including metadata and failures, is transferred as 8 KiB base64 chunks in separate calls, hash/length checked and released. |
| T20 | info.py | Both upstream fractional UPM tests produce info.unitsPerEm.fractional, with zero unclassified failures. |

The empty-shape equivalence is named fontlab.save.emptyShape. Receipt comparison
notes disclose both semantic exclusions; root-level active and decorated empty
shapes remain significant. Glyph history is observed instead of package-only
state. The native history probe is source-based, pending C4 confirmation.

## Read-only native source evidence

Root: `<FontLab C++ source checkout>` (FontLab Ltd. internal, read-only).

- Proteus/common/model/flshape.cpp:4635–4639 delegates clearContours to shapeData;
  flshapedata.cpp:3247–3261 clears contours without marking changed.
- flshape.cpp:520–547 changes the transform property; explicitly marking the
  shape changed makes the owning shape participate in the history request.
- Proteus/pygate/pyflobject.cpp:313–317 binds historyStates/currentHistoryState.
  Proteus/common/controllers/flhistorycontroller.cpp:2145–2165 walks glyph,
  layer, shape and shapeData indices; package-only history omits glyph edits.
- Proteus/pygate/pyflitems.cpp:134–159 maps a notification list to native objects.
  Glyph mutation now sends the same [layer, glyph] list before editing and in
  finally afterwards, including partially failing mutations.

The requested round-12 review file could not be located in the workspace reviews
directory or WORK.md. All four explicit review instructions in the Round-13
brief are implemented: closing notification finally, pending-point lifecycle
boundaries, an all-offcurve closed contour regression, and key-master scope.
