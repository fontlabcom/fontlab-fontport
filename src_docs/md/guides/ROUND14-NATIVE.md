---
this_file: src_docs/md/guides/ROUND14-NATIVE.md
---

# Round 14: geometry history and independent Undo evidence

C4 measurements on 94b266a refute the previous geometry Undo claim. Round 13's
changed flags alone do not protect shape references retained by native history.
This round implements the existing, natively measured Glyport copy-on-write
protocol, but Fontport's result still needs C4 verification. No native session
was run by this host-free lane. Round 13 was landed by the controller as e2ca6ec;
these changes are on top and are not committed by this lane.

## T10: protected shapes, two explicit history rows

After the pre-change [layer, glyph] notification, clone each working shape and
replace it at the same layer index. Mutate only the clones, then send the same
notification list in finally. The flLayer/flGlyph objects remain the same;
their history keeps the old shapes. Shape style and transforms are cloned;
other layers and layer-level hints are not replaced. Hinted/shared/transformed
outline cases retain their pre-write refusals.

The two notifications produce a measured extra no-op checkpoint. Fontport exposes
this as glyph.exactSingleUndo: supported=False, rather than claiming one row.
Driver receipts retain one_history_row, accept only one or two rows, and name
glyph.exactSingleUndo when two appear. The FIRST Undo must restore geometry.
For a two-row edit the second Undo must leave that baseline unchanged; Redo of
the checkpoint must also leave it unchanged, then Redo of the edit restores the
edited geometry. More rows or any geometry mismatch fail the suite.

Read-only source root: `<FontLab C++ source checkout>` (FontLab Ltd. internal, read-only).

- Proteus/common/model/fllayer.cpp:1393–1430 initializes shape histories and adds
  shape objects to history-state storage; those references must remain intact.
- flshape.cpp:2173–2233 clones shapeData, transform and style; clone() delegates
  to cloneCustom(cloneAll). fllayer.cpp:9546–9566 exposes insertShape/removeShape.
- flobject.cpp:2816–2850 restores stored history records. Package initialization
  at flpackage.cpp:14377–14396 covers package containers, not a deep geometry copy.
- Proteus/pygate/pyflitems.cpp:134–159 maps notifyChangesApplied's object list;
  pre/post notification alone cannot isolate mutable shape data.
- Existing Python route: fontlab-glyport/src/fontlab_glyport/model/
  fontlab_backend.py:1559–1604 (_prepare/_own_shape).
- Native evidence: workspace verification/issue-101-ecosystem/evidence/
  glyport-model/probe_undo_first_edit.json (pre-notify gives a restoring Undo plus
  a no-op row), and glyport-matrix/probe_undo_cloned_shape.json (in-place mutation
  never restores; clone restores on first Undo). These contradict the suggestion
  that mutating the original shape protects its saved snapshot.

## T22: independent MCP geometry oracle

Every baseline/read uses a fresh fontpr get_glyph call, detached with deepcopy.
Before editing, freeze a JSON geometry record from every layer's elements
(including contour node/point data and component transforms). Undo/Redo receipts
include expected/observed geometry strings, SHA-256 hashes and geometry_equal.
False geometry_equal fails even when equal is true. Required geometry edits must
also actually change this record, preventing a no-op from passing restoration.
Raw MCP payloads remain in receipts. Only the documented bare empty-shape and
layer-active UI equivalences are applied. Unit tests deliberately corrupt node
coordinates and prove the receipt is retained as a failure.

## T21 and structured scope

Native writes that cannot satisfy UFO per-side kerning membership refuse as
groups.multiMembership before any checkpoint or write. Detached generic groups
still raise their usual validation error. The both-sided native refusal probe
creates an owned glyph with no pre-existing class membership and tests divergent
sides using an empty side; it no longer corrupts A's memberships on plum.

Panose, weight/width and H/V stem snaps retain key-master default semantics.
Both capabilities() and STRUCTURED_ROUTES expose bound: key-master for each.
Per-master writes were not added: only the current key-master write routes have
C4 Undo/Redo/VFJ proof. The catalogue does not imply all-master writes.

## C4 commands

Run in fresh sessions using the shared wrapper; fixtures and outputs are owned.
The wrapper locates the workspace and handles the mutating-session policy.
Each edit/action/read/checkpoint is a separate call under the existing 4-second
gate. Owned fonts close with save=False in cleanup.

```sh
sh tests/native_drivers/run-round10.sh --suite glyph
sh tests/native_drivers/run-round10.sh --suite pens
sh tests/native_drivers/run-round10.sh --suite boundaries
```

Repeat all three with --fixture and an absolute GetGo cc0/plum/plum-var.vfj path;
the default is cc0/medi/medi.vfj. Glyph now covers edit_glyph, live getPen,
appendPoint, width, clearContours, component add/transform, and hinted refusal.
Pens must prove rounded flatten geometry restores. Boundaries must prove no
multi-membership setup exception and key-master scope in capability receipts.
Re-run the seven suites and attached upstream as a regression sweep; append
--dry-run to validate startup without host contact.
