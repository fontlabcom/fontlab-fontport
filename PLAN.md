---
this_file: PLAN.md
---

# Remaining work

Start with user-visible UFO feature and batch-recipe behavior across Fontport, App and Scriptmix. Check affected providers and consumers together. Keep FontParts, DesignSpace and UFO adapters in Fontport, UI and script helpers in App, and Glyphs compatibility in Glyport. Preserve upstream object identities, complete inputs and exact feature source. App consumers use the public `capabilities()` and `invalidate()` interfaces. Menu lookup and failed synchronization belong in App. The affine and UFO routes do not promise arbitrary interpolation or stem preservation.

Use focused checks during implementation. Keep source review, ordinary installed artifacts, released consumer behavior, native history and publication as separate results. Use the arm64 Python 3.11 checks in README, the existing 80% changed-module gate and the normal delivery hooks. Static, variable and non-Latin fixtures cover different native failure modes. Record installed versions and import origins and keep private fixture data out of upstream reports.

## Features and batch recipes

- Reconcile UFO feature source and batch-recipe behavior across the three packages. Qualify the exact feature-source integration from matching artifacts through native history and saved/reopened files. Literal U+2029 editing needs its own successful round trip.
- For workflow 17 P2, finish post-change graph analysis, controller and ledger review, commit-bound strict docs, reviewed main integration and exact-commit CI/output lineage. Preserve recipe-only No Font operation, explicit external Python selection, case/Unicode containment and no-overwrite checks. Keep complete inputs and independently verify reopened geometry and resources.
- Test matching P2 archives in two fresh prefixes, then exercise the actual consumer, history, Undo/Redo and reopen. Check separate editor and panel close acknowledgements, terminal child/stdout/scratch cleanup, active-window isolation, dispatch/scheduling retries, the existing read budget and the first-EAGAIN stop without losing the next poll's data. Eight of the minimum eighteen workflows have source qualification. The ledger records zero workflows at full parity and retains all 8,723 obligations.

## Releases and installed consumers

- Issue 271 still needs confirmation of the independent cohort review and required hooks, followed by serialized macOS/Windows installer checks. Preserve owner files through conflicts and partial failure.
- Issue 254 needs the installed Pens floor checked on every supported Instamix route, including a stale sibling checkout and fallback without uv. Verify that compatible Pens supplies `FONTGATE_NODE_TYPES` and an older installation cannot silently satisfy `fontlab-python-pens>=1.0.0`.
- With the released Fontport installed in FontLab 9, compare `glyph_summaries` Unicode values from layer targets with the package values and measure TMetrics typing on the same font.
- Issue 255 needs explicit D43 recovery and admission for released FontLab checks. Install matching Fly >=1.3 separately. Exercise generated startup recipes, all three Scripts report windows and the original UFO/UI/history/reopen workflows. Preserve open documents.
- The existing lock selects the sibling editable App and the declared floor is 1.2.0. Confirm the reviewed App release and the owner’s intended lock source before refreshing the optional integration metadata.
- Qualify the lint repair and portability/licence changes against whole-current-App behavior, default resolution and genuine final wheel/sdist cohorts. Inspect payloads, licences and privacy, install into clean prefixes, and run extracted tests. Preserve default editing/save behavior and opt-in strict history/persistence.

## Native adapters and object lifetime

Issue 123 remains paused. Keep Issue 207 candidate reconciliation separate from canonical adoption. Issue 210 describes the future plugin split, Issue 211 retains follow-ups, and Issue 214 is the preparation catalogue. All private Pages holds remain in force.

- Reconcile Issue 207 with the current DesignSpace/UFO/fontParts boundary and preserve host data and origin guards. Qualify object lifetime, full-font history, failure paths and saved/reopened data through matching installed consumers.
- F1 I1 needs native duplicate-owner checks in both orders using stored `fgFont.keys()` names. Measure whole-font enumeration cost before changing repeated lookups. Verify registered-record Unicode writes on noncurrent fonts through no-op, refusal, Apply, Undo, Redo and reopen, preserving native-global notes, lib and unrelated fields.
- Check the shared canvas-history guard for glyph and auxiliary-layer writes and new glyph creation. Compare complete font/history snapshots for Font-window, canvas-owner, wrong-package, unreadable and off-thread cases. Package metadata/groups/features and detached transfer have separate ownership.
- Qualify all six App editor factories in FontLab, including apply/cancel, callbacks, refresh, close, deferred teardown and group/kerning sequence placement. Exercise active-font feature I/O with stale sources, inactive fonts and missing references, then verify master restoration and VFJ reopen.
- Qualify world registration, open/new/current/close ownership, refresh, selection/events and actual dirty/source-path semantics after save. Exercise affine preview, native axes and axis maps, batch cancellation/UI scheduling and reopened outputs.
- Recheck the documented live FontParts capabilities against the [1,797-row coverage ledger](src_docs/md/guides/FONTPARTS-COVERAGE.md). Preserve both classification columns, exact reproducers and the three fixture families for changed or unresolved behavior.

## Geometry and resources

- Issue 241 needs the TGlyph several-shape contour edit on an owned font. Check the supported unshared, untransformed contour shape, its neighboring shapes, whether the edit creates exactly one Undo row, Undo/Redo and VFJ reopen. Before widening refusals, check transformed shapes/layers in layer coordinates, every glyph sharing a shape, contours split across shapes or added without a contour shape, and component identity/transform on combined edits. Compare shape count, order, names, flags, notes and unrelated layer data. Check fractional anchors at 10.5/20.25 and hinted outlines with TrueType data through reopen.
- Recheck fractional pen writes after a fix for fontlab/fl#8638 or a change to direct node positioning. Switch between fonts with Round coordinates on and off and read the seeded coordinates back. Repeat the r31 native Redo comparison with the existing 1e-3 tolerance, including a genuine 0.1 difference.
- Independently qualify the isolated Task6c staged PNG/color transaction on current source and full-font packages/zips. Check faults, rollback, stale sources, handle lifetime, and native/no-resource writer limits. Complete ImageSet/DataSet collections and native resource parity, including resource loss in a parentless glyph copy.
- Qualify native multilayer, guideline and image interchange and detached orphans. Compare reopened outlines, node types, references and metrics. Document reviewed exclusions and file a privacy-safe FontLab issue for a reproduced upstream defect.

## Metadata, groups and kerning

- Issue 250 N3 needs a reliable signal or conservative refusal after Undo followed by an unrecorded edit clears Redo. Check the missing stem-snap history row on FontLab 9809. After fontlab/fl#8633 is fixed, verify active, inactive and dirty documents through Undo/Redo before relaxing the guard.
- Compare D18-2's eight read-only vertical metrics with Font Info and decide whether to support export or writes. Verify integral `unitsPerEm` readback in the live host. Check optional metric clearing, changing name records, key-master fields and exact one-row metadata history.
- Check the printable-ASCII group-name limit, divergent both-sided classes, dependent-pair validation and global group loss across VFJ save/reopen. Keep explicit zero kerning distinct from absence.
- Verify installed kerning/editor integration and per-master write/history limits (fontlab/fl#8639 and fontlab/fl#8640). With Light current in a fresh Plum copy, check that the editor names Regular as the default target. Inspect noncurrent-master writes through Undo/Redo/reopen and preserve fractional values on every master before widening support.
- Qualify structured native feature and JSON-compatible packageLib writes through history and persistence. Retain lossless-source requirements and the arbitrary-text and binary/date refusals.

Once a milestone is integrated, check current branch/worktree attachments and retain unique, recoverable work before removing anything obsolete. See [TODO.md](TODO.md) for individual checks.
