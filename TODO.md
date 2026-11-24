---
this_file: TODO.md
---

- [ ] Issue 271: independently review and integrate the generated installer through repository gates, verify exact-SHA CI/archives, and qualify macOS/Windows native execution after serialized admission.


## Next steps (prioritised, 2026-11-17)

1. P0 live FontLab 9: check `glyph_summaries` unicodes and TMetrics speed with released v1.2.14 installed.
2. P0 reconcile UFO feature and batch-recipe behaviour across Fontport, App and Scriptmix (source only).
3. P1 qualify released Fly/Fontport scripts natively (Issue 255); the three Scripts demo report windows.
4. P1 reconcile the Issue 207 candidate; verify the pens floor `>=1.0.0` on every install route.
5. P2 native rows tracked in fl issues: fl#8633 (stem-snap Undo/Redo), fl#8638 (Round coordinates on fgShape to flShape), fl#8640 (kerning Undo rounds every master), fl#8639.
6. Test and qualification rows are at the end, deprioritised (owner: functional progress first).

- [ ] Live-check `glyph_summaries` unicodes (layer target) against package-level unicodes in FontLab 9, and TMetrics speed with the released fontport installed.

- [ ] Reconcile UFO feature and batch-recipe behavior across Fontport, App and Scriptmix with focused source/preservation checks before the detailed artifact and native/history pass.

- [ ] Native (open question only): whether `flPackage.kerning(<non-current master>)` accepts writes with working Undo/Redo and reopen. Fontport writes only the default master, so this bounds any future per-master kerning target. Upstream: fl#8640 (Undo rounds fractional kerning on other masters) and fl#8639 (reopen rounding); see `reports/a2-live-report-39.md`.
- [ ] D18-2 owner-run: the live readback of the eight vertical metrics passed (A2 report 21); compare the values with the Font Info dialog (expected Typo 765/-235/200, hhea 965/-235/0, win 965/235) and decide whether export/`set_info` should cover these read-only fields (currently read-only, not exported).

# Open tasks

- [ ] Issue 255: After explicit D43 recovery and admission, qualify released Fly/Fontport Scripts, generated startup recipes and original native UFO/UI/history/save-reopen workflows with exact installed paths and provider identities.

- [ ] Issue 250 N3 gap: a stem-snap write after the document's history was undone and then cleared (Redo removed by an unrecorded write) reads `__has_history_changes` None, so `set_info_many` does not refuse it, yet even a notify-bracketed write gets no Undo row and a later info Undo resets the stems (A2 report 12, `r12_n3c7-12.json`). Find a native signal for undone history or refuse stem writes unconditionally; recheck on FontLab 9809.
- [ ] Issue 250 N3: once FontLab fixes the stem-snap setter (Fontlab/fl#8633), relax the `info.postscriptStemSnap.history` refusal and re-verify live Undo/Redo on active, non-active and dirty documents. Native issue: https://github.com/Fontlab/fl/issues/8633 (related: #8631 set_active_glyph, #8632 fgSymbol no-arg crash).
- [ ] Verify on live FontLab 9 that `get_info("unitsPerEm")` reads back as `int` (source coercion is done and unit-tested; native readback unproved).

- [ ] Packaging floor: fontport b097603 and later imports `FONTGATE_NODE_TYPES` from `fontlab_pens`, first exported in pens v1.0.0 (d8cdd7e). The declared `fontlab-python-pens>=1.0.0` covers it, but FontLab installs that resolve an older pens (on 2026-11-11 the FontLab site-packages held pens 0.1.0 metadata) fail with ImportError; make the installer enforce the floor and install pens together with fontport, then verify in FontLab. Diagnosis 2026-11-12: `install.vfpy` already installs a `fontlab-python-pens` checkout found beside fontport (`install_siblings`) and sends other requirements to `uv pip install`, which enforces `>=1.0.0`. The gap is the sibling route: `install_siblings` runs the sibling installer without comparing its pyproject version to the requirement, and the no-uv fallback `missing()` checks presence only, so an old pens checkout or an old installed pens passes. Fixing it changes the byte-identical shared `install.vfpy` (seven copies, `tools/check_install_copies.py`), so it is a feature change owned by the install.vfpy propagation queue: land it in App first, then propagate; do not edit this copy alone.
- [ ] Qualify the isolated Task6c staged PNG/color transaction with full current source/ordinary package/zip, fault/lifetime and independent review before unrelated production work.
- [ ] Complete full ImageSet/DataSet collection and native resource parity; checked detached PNG data success does not close those obligations. For a reproduced upstream blocker, track the upstream defect in a privacy-safe fl issue (issues only, no pull requests).

- [ ] Reconcile the Issue 207 candidate with the current DesignSpace/UFO/fontParts boundary; preserve all host data and origin guards.
- [ ] Qualify native object lifetime, full-font history, Undo/Redo, failure paths and saved/reopened artifacts through matching installed consumers.

- [ ] Qualify F1 I1 native keys enumeration preservation and whole-font read timing; source tests reject either duplicate ordering, but each lookup scans all glyph names.

- [ ] Qualify the registered-record Unicode read/write repair on ordinary installed artifacts: full saved-font note/lib preservation, noncurrent target, no-op/refusal, Unicode Apply/Undo/Redo/reopen; retain complete unrelated fields and native-global note semantics.
- [ ] Qualify the shared canvas-history guard in native glyph writes, auxiliary-layer add/remove and new-glyph creation using owned fixtures; verify complete snapshots, history, Undo/Redo and reopen. Package info/lib/group notifications remain outside this glyph-owner guard.
- [ ] Coordinate App qualification of all six restored UI factories in FontLab: apply/cancel, callbacks, group/kerning sequence integration, refresh, close and deferred teardown.
- [ ] Coordinate App qualification of active-font feature I/O in FontLab: inactive/stale/missing-reference refusals, master restoration, Undo/Redo and VFJ reopen.
- [ ] Select the reviewed App release and agree the lock source; then refresh the optional FontLab integration metadata in uv.lock.
- [ ] Complete native geometry/component/anchor/layer writes with Undo/Redo and preservation of hints, raw flags, notes and unrelated data; retain measured exclusions.
- [ ] Owner smoke (Issue 241): in TGlyph, edit contours of an owned glyph whose layer has several shapes (one contour shape plus components/images), Apply, and verify the other shapes are unchanged, the history shows the edit, Undo/Redo restore it and save/reopen keeps it.
- [ ] Owner smoke before widening transformed contour shapes or transformed layers: edit, Apply, compare reread outline in layer coordinates, Undo/Redo, save/reopen.
- [ ] Owner smoke before widening shared contour shapes (referenceCount>1): edit through one glyph, inspect every sharing glyph, Undo/Redo.
- [ ] Owner smoke before widening contours spread over several shapes or added to a layer with no contour shape: verify shape count, order, names, raw flags and notes through Apply/Undo/Redo/reopen.
- [ ] Owner smoke before widening component changes combined with contour edits on several-shape layers: verify component identity/transform through Apply/Undo/Redo.
- [ ] Owner smoke before widening fractional anchors: write 10.5/20.25 anchors and compare native readback before and after save/reopen.
- [ ] Owner smoke before widening hinted-layer outline edits: compare hints and TrueType data after Apply/Undo/reopen.
- [ ] Resolve exact one-row metadata history, optional metric clearing and persistent changing name-record writes; recheck structured key-master fields.
- [ ] Resolve native group name, both-sided divergence and legacy-group VFJ persistence boundaries.
- [ ] Qualify installed kerning/editor integration (the editor is in `fontlabapp.fontui` since issue 201) and resolve fractional Redo without silent rounding.
- [ ] Qualify native structured feature and packageLib history/persistence; retain explicit arbitrary-text and binary/date limits.
- [ ] Complete native multilayer/guideline/image UFO interchange and detached-orphan compatibility, or document reviewed exclusions.
- [ ] Re-run changed and unresolved native cases on static, variable and non-Latin fixtures; retain exact reproducers and host-defect receipts.
- [ ] Complete native world ownership/refresh, selection/event subscriptions and save-state/source-path integration.
- [ ] Qualify affine preview, native axis inspection, batch cancellation/UI scheduling and reopened generated artifacts.
- [ ] Audit final wheel/sdist payload, licences and privacy; verify clean installs, extracted tests and installed native behaviour.
- [ ] Complete acceptance of the live FontParts environment against its documented capabilities and owned-font results.

- [ ] Qualify the final clean cohort wheel/sdist and ordinary installed tuple after the scoped portability/licence change; retain installed native and release gates.

- [ ] Retain default/strict editing and save contracts while checking new consumer tuples.

- [ ] Complete applicable native whole-font/history/round-trip and cohort-version acceptance.

- [ ] Qualify the three Scripts demo report windows in FontLab using the installed Fly/App reporting API; preserve open-document state.
- [ ] Pen writes can round fractional coordinates: `host._stage_shapes` (src/fontlab_fontport/host.py:431) converts fgShape to flShape with `assign`, and FontLab applies "Round coordinates" from app-wide state that follows neither the target nor the current font (fontlab/fl#8638). Example: 10.4/410.6 is stored as 10/411 in a font whose setting is off. Next check: once FontLab fixes this, or after a Fontport change that writes node positions directly (`flNode.position` kept fractions in every run), read back seeded fractions in on and off fonts after switching fonts.
- [ ] Live r31 rerun: confirm that the owned-host drivers' tolerant comparison (`values_close`, `READBACK_ATOL` 1e-3 in `tests/native_drivers/round10_payloads.py`) passes a real Redo read-back (float32, 10.4 -> 10.3999996) and still flags a real 0.1 change.
- [ ] Native (F47-1, owner): on a fresh copy of the plum font with Light as the current master, confirm the Fontport kerning write text names the default master (Regular) instead of asking to make Light current (App `kerning.py` lines 47-58).
- [ ] Native (Issue 254, owner): after the App `install.vfpy` (main at or after 5cac0d6), install Fontport and confirm the pens floor `>=1.0.0` holds on every install route (see row 21).
- [ ] Licence audit (Issue 250, owner Q5): `pyproject.toml` and `LICENSE` are already Apache-2.0 and the only two SPDX headers read Apache-2.0. Nothing is known to remain; verify README/NOTICE wording carries no MIT/older-licence claim for FontLab-authored code, then close this row.

## Deprioritised qualification and test-infrastructure rows

- [ ] Qualify whole-current-App and default-resolution behavior plus final ordinary distributions for the delivered lint-repair cohort; retain existing native, adoption, canonical and publication gates.
- [ ] Complete #17 P2 post-change graph, exact ledger/source qualification and staged review; refresh actual main, reconcile intervening changes, qualify genuine-commit docs, then verify normal hooked main delivery, exact-commit CI and generated-output lineage.
- [ ] Qualify #17 P2 matching ordinary artifacts, two fresh prefixes and archives, then its actual consumer/native/history/Undo/Redo/reopen checks; retain recipe-only No Font, complete input/output preservation, distinct cleanup ACKs and actual terminal worker cleanup. Keep wider literal-U+2029 feature editing, canonical adoption, publication and private Pages holds as separate workflow gates.
- [ ] Qualify matching ordinary artifacts and owned native/history/reopen checks for the source-qualified combined-main exact UFO feature-source integration; full literal paragraph-separator editing remains separate.
- [ ] Run the exact repository checks on the integrated source, obtain independent review, commit/push the scoped milestone and verify its remote head.
- [ ] After qualified main integration, inventory obsolete branches/files, preserve unique work and remove only proven stale items with recovery evidence.
- [ ] Review the complete catalogue/source-doc relocation and qualify source X plus a rebuild at its actual epoch through normal main Actions.
- [ ] Verify immutable generated Y and retain all private Pages operation holds and separate native/owner-install gates.
