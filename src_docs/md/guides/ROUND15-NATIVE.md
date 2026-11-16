---
this_file: src_docs/md/guides/ROUND15-NATIVE.md
---

# Round 15: driver-only comparison corrections

Input: workspace verification/issue-106/evidence/issue-105/round14/SUMMARY.md.
C4 verified native geometry restoration on f3d7dc5, including the named extra
no-op row. This round changes only driver oracles and their tests/docs.

- T23: glyph_receipt compares upstream point-pen digests, numeric metric values,
  Unicode lists, lib and anchor dictionaries directly, without serialization or
  numeric tolerance. Only None/absent and empty notes are equivalent, disclosed
  as fontlab.note.empty. fontlab.numericValue documents value equality (0 equals
  0.0). Raw expected/observed values, digests and anchors remain in receipts.
- T24: glyph-create explicitly selects package history (currentHistoryState and
  historyStates); later mutations select glyph history. Receipts record scope.
  Creation Undo/Redo/reopen still compare complete payloads and frozen geometry.
- T25: fontlab.lastModified excludes the root MCP save/edit timestamp from read
  equality. Raw timestamps remain in expected/observed receipts. No nested lib
  key is removed. Other metadata, outlines and metrics remain significant.

Regression probes change an outline point, width, height, nonempty note and a
nested lastModified lib value; each must fail equality. Creation receipts are
exercised with package rows present and glyph history inaccessible, proving the
scope switch rather than merely testing the helper in isolation.

C4 re-runs (each wrapper command uses an owned fixture/session):

```sh
sh tests/native_drivers/run-round10.sh --suite glyph
sh tests/native_drivers/run-round10.sh --suite interchange
```

Repeat glyph with --fixture and an absolute GetGo cc0/plum/plum-var.vfj path;
repeat interchange with absolute paths to cc0/plum/plum-var.vfj and
apache/zotosans/zotosans-georgian.vfj. Medio is the default. Expect no false
creation-history, timestamp, empty-note or numeric-type failures, while geometry
Undo/Redo/reopen and import/export comparisons remain mandatory. Every phase
retains the existing time limit and size-framed transfer. Append --dry-run for
host-free wrapper validation. The remaining suites are regression checks.
