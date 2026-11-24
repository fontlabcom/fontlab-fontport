---
this_file: CHANGELOG.md
---

## Unreleased

- Site now uses the fly-january 0.2.1 theme (chrome: fontlab).

## 2026-11-18 — Issue 271 installer source alignment

The generated installer matches the reviewed Instamix 1.0.18 template: it requires
conflict preflight support, selects compatible local wheels and reports completed
work before an installation failure. Exact reviewed-template byte parity and import-sentinel/wheel-order smoke checks pass. Existing focused installer tests pass (exit 0, 0.74 seconds).
Consumer integration, released archives and native execution remain separate checks.

## 2026-11-17 — Installer stub from instamix 1.0.15 (Issue 259 follow-ups)

- `install.vfpy` is now the stub from fontlab-python-instamix 1.0.15. It replaces an
  installed instamix older than 1.0.13 and puts the old copy back if the upgrade
  fails; linked checkouts and local builds are kept. A download that fails for
  lack of root certificates (FontLab 9 for macOS) is retried with the system curl.

## 2026-11-17 — Task-list cleanup (Issue 258)

- Installer-chain rows (Task40 review, Task29 sdist contract, guarded common installer, shared-installer delivery, sdist installer fix, false-marker sibling staging) are closed. Evidence: `install.vfpy` is the fontlab-instamix stub since 1.2.12 (this file, 1.2.12 entry); the sdist installer fix reached main `517a7e06626dc49f93f2a9ab6767d0a23f127d00` with CI 43658462711; `3db99b4` (guarded installer refresh) passed CI 44067859935; v1.2.13 and v1.2.14 are tagged and released (v1.2.14 latest, 2026-11-17).
- The Release workflow run 44068119420 at `d441162` failed (trusted publisher not registered for PyPI); recorded in the Issue 256 publisher list, not a source defect.
- Fix-PR wording for Proteus/FontGate/pyfontgate rows removed; defects are tracked as fl#8633, fl#8638, fl#8639, fl#8640 (issues only). Test and qualification rows moved to the end of TODO.md.

## 2026-11-17 — Guarded installer source qualification (Task40)

- The complete normal source hook passes: 5,150 Fontport tests, two existing
  optional skips and 63 retained warnings; 872 required Pens tests pass with
  95.22% coverage. The complete changed `live.py` module reaches 95.51% combined
  statement/branch coverage against the unchanged 80% gate.
- Retained name iteration in the glyph-summary fallback with a local lint
  explanation, sorted its regression imports, and restored the existing README
  installer paragraph in the documentation index. Expanded Ruff and all 37
  hash-locked Python 3.13 documentation tests pass; runtime AST is unchanged.
- Initial Pens parity, lint and documentation-source failures remain recorded.
  The final source cohort uses the reviewed Pens installer/oracle successor.
  Graph/review, delivery/CI/release, installed/native/Windows and owner recovery
  remain separate; standalone Fly, Aidus, private Pages and paused-work holds remain.

## 2026-11-17 — Fontport installer contract source fix (Task29)

- The sdist contract now requires the current canonical FLM header and exact
  stub SHA-256, preserving byte parity, Instamix handoff, canonical fallback,
  archive identity, version and installer table checks.
- The normal complete boundary module reproduced the stale-header failure
  (one failed, nine passed) and then passed ten tests in 0.55s. Two genuine
  sdists were read without executing their installer or installing a consumer.
- This is an uncommitted six-file source successor only. Independent review,
  full cohort/hook, delivery, release, installed and native checks remain open;
  existing owner-recovery, Aidus/Fly, private Pages and paused-work holds remain.

## 2026-11-17 — Guarded common installer source candidate

Copied the exact canonical common template shipped with Instamix 1.0.11.
Provider reuse now requires migration/rollback capabilities and entry context is
checked before bootstrap. Legacy rollback requires 1.0.9 or newer; the entry
guard originated in 1.0.10, and shared-layout venv reuse requires 1.0.11.
No package metadata, dependency floors, scripts, bundles or licences changed.
This supersedes earlier shared-installer source notes; historical checks retain
their dated scope.

Compile/AST and exact-template byte checks qualify source only. No installer,
provider, readiness harness, test, package build or native operation ran.
Consumer execution, owner recovery and delivery remain held. Required broad
cohort/suite, release, installed and Windows/native gates remain open.


## 1.2.12 (2026-11-16)

- `install.vfpy` is now the short fontlab-instamix stub. It installs
  fontlab-instamix from PyPI when it is missing, then installs this checkout from
  its `[tool.fontlab-install]` table. The large legacy installer is gone.
- `tests/test_package_boundaries.py`: the sdist test checks the stub instead of the legacy installer's version handling.
- README describes the stub install.
## 2026-11-14 — Functional work order documented

- Added the owner's functional-progress-first guidance and repository-specific priorities, including cross-package compatibility and a later detailed testing pass. Existing mandatory hooks, holds and unfinished work remain in force.
- This change updates guidance and planning only; it establishes no new runtime, installed, native or release result.

## 2026-11-16 — Fast glyph reads for live fonts

- `LiveFont.__contains__`, `defaultLayer` and the live glyph run read FontLab names and the default master directly, without building FontParts glyph wrappers. Backends gain `has_glyph(name, layer)` and `glyph_summaries(layer)` (name, unicodes, advance width) for the FontLab, memory and UFO hosts; groups reads are faster. This removes most of the per-key cost of TMetrics typing (0.85 s to about 0.13 s per key on Lato, measured live with the lane source).
- Full suite: the same 25 failures as the unchanged baseline HEAD, nothing new; new `tests/test_fast_reads.py` passes. Independent review approves. Open live check: unicodes read from the layer target in `glyph_summaries` against package-level unicodes.

## 2026-11-15 — Shared installer source alignment

Copied the reviewed shared installer exactly: dependency constraints and managed origins remain protected; inactive conditional dependencies are filtered before sibling execution in the resolver target Python. FontLab imports remain standard-library-only. Package identity, runtime APIs, dependency declarations, scripts, bundles and legal files are unchanged. Existing source-archive installer selection is retained.

Focused checks: 10 passed in 0.61s. This qualifies the local source candidate only. Independent review, combined-main/full delivery gates, genuine release/downloads, installed provider closure and admitted FontLab/native workflows remain separate. No owner-folder installation or native operation ran.



## 2026-11-15 — Source archive includes the installer

Added `install.vfpy` to the sdist allowlist; its bytes and mode are unchanged.
A real source-build regression reproduces the omitted member before the fix
and passes afterward, checking exact installer bytes, FLM marker and genuine
PKG-INFO version lookup without running the installer. All ten focused boundary
tests pass (0.54s). This proves the local source archive input, not the future
v1.2.10 release payload or installed/native behavior. Separate reviewed source
propagation reached main `517a7e06626dc49f93f2a9ab6767d0a23f127d00` with
controller-qualified normal delivery and exact-commit CI 43658462711.

## 2026-11-15 — Shared installer source parity

The source installer matches the reviewed shared template byte for byte while
retaining mode 0644. Original requirements now reach uv with installer-managed
version/origin guards; optional dependency metadata is generated and
unverifiable no-uv requirements fail before mutation. Nine existing offline
package-boundary checks pass; package metadata and runtime providers are
unchanged. This records source-copy qualification only. Independent review,
controller delivery/full gates, cohort propagation, release and installed/native
acceptance remain separate. False-marker local sibling staging remains open.

## 2026-11-13 — Documentation content oracle delivered

The reviewed content-oracle repair reached upstream main in merge
`9b31d13fa950a39e52f5327b594f007fb801a6f8`, preserving main `630edf16`
and repair `c3dd1c5`. Independent source and delivery reviews passed. Direct
controller gates passed: 5,130 source tests, one existing skip, 92.30% combined
coverage; 37 locked documentation tests; expanded source/tests/examples/Scripts
Ruff; the external 60-file documentation build; and 869 Pens tests.

The ordinary installed pre-push gate passed separately with 5,129 source tests,
two skips and 869 Pens tests. Its extra skipped case is not identified by the
saved summary. The first push failed for absent upstream tracking; only the
owned branch tracking was added before the normal non-force retry succeeded.
Exact-commit [Documentation run 43506136865](https://github.com/fontlabcom/fontlab-fontport/actions/runs/43506136865)
passed both build and qualify-generated-output jobs. Actual main readback
matched the merge after CI. Only this solved integration item leaves PLAN/TODO.

Graph UNKNOWN impact and omitted flows, historical preservation failures and
untraced writers remain unresolved. These source/main/CI results establish no
new release, artifact, installation, native or default-resolution acceptance.
Existing native, private Pages and Issue 123 holds remain unchanged.


## 2026-11-13 — Documentation content oracle

The cross-date rebuild test checks an explicit content patch against the index,
avoiding a filename-only false positive when automatic index refresh is disabled.
The complete file hashes, 60-file count, source epoch and parity assertions remain.
One regression covers unchanged bytes with changed timestamps, byte changes,
deletion, executable-mode changes and the existing staged/index baseline. Every
case preserves raw fixture index bytes and mode. The old command fails the new
regression and original cross-date test; the content patch passes both.

The locked Python 3.13 documentation suite passes all 37 tests; the exact shell
entrypoint builds 60 files in external scratch. Arm64 Python 3.11 source checks
pass 5,130 tests with the existing external-corpus skip; combined coverage is
92.30%. Source/tests/examples/Scripts lint passes. These are isolated source
results; independent review, combined-main delivery and exact-commit CI remain.

## 2026-11-13 — Issue 255 verified release qualification

- [fontlab-fontport v1.2.9](https://github.com/fontlabcom/fontlab-fontport/releases/tag/v1.2.9) is released at `a11cbe2340201ec07d81c95dd567981cdef81d12`. Reviewed main/tag delivery, applicable CI and actual downloads match the qualified artifacts.
- The three Scripts, seven examples and generated startup/recipe teaching use Fly. The UI tombstone teaches fly.ap.fontui with unchanged runtime ownership/error behavior.
- 5,131 source tests pass without skips; the complete tombstone has 100% statement/branch coverage with zero exclusions. All 36 documentation tests and exact 60-file containing-source rebuild parity pass. Genuine wheel and actual-sdist ordinary cohorts each contain 28 compatible packages and match all 43 installed Fontport payload files; three lazy Scripts, UFO geometry and 23 archive/tombstone cases pass.
- Ordinary external installation is qualified; installed FontLab/native acceptance remains unproved under D43. Consumer setup still requires separately installing matching Fly >=1.3 in the same interpreter. Provider source installers do not automatically supply or enforce this prerequisite; no reverse mandatory Fly dependency is claimed.

## 2026-11-13 — Issue 255 residual UI migration teaching

The removed UI migration example uses `fly.ap.fontui`; canonical ownership,
MOVED_HOME/error text, finder and runtime AST outside the docstring are unchanged.
README/index now disclose that source installation copies Scripts but does not
supply/check Fly. Install a matching Fly >=1.3 cohort separately before Scripts
or generated startup recipes; the Fontport library adds no Fly dependency.

The teaching regression fails on the old import. All53 focused tombstone checks
pass afterward; the complete changed module has 25/25 statements and 6/6 branches
covered, with zero exclusions. Final full source 5,131 passed / 63 warnings on arm64
Python 3.11.14. Initial baseline 5,130 passed/one optional skip lacked the external
Examples peer; supplying that peer enables the existing read-only 99-VFJ GetGo
check. All 99 corpus bytes match the reviewed Examples source. No fixture changed.
Ruff 0.17.5 passes source/tests/examples/Scripts. Hash-locked external strict docs
build and 36 tests pass; a second clean build has exact 60-file parity. Shared
installer, dependency metadata and product generated docs remain unchanged.

## 2026-11-13 — Issue 255 Fly example source migration

- Route three Scripts and eight direct imports across seven examples through
  `fly.fp`; keep the genuine external FontParts world protocol unchanged.
- Emit Fly startup and affine recipe source without changing library runtime
  dependencies, exclusive output writes, source-origin guards or registration
  lifetime. Update supported authored snippets and the Fly 1.3.0 prerequisite.
- Prepare the real sibling Fly finder only for source tests. Preserve actual
  provider identity, all 19 numbered examples, generated-source execution and
  refusal assertions; tighten two existing blind exception tests to the measured
  UnsupportedCapability class and mechanically repair two existing Ruff findings.
- Explicit Python 3.11 arm64 source suite: 5,130 passed, one existing optional
  skip, 63 warnings. Complete changed-module coverage: Scripts/examples/deploy
  100%, recipe 94%; source/tests/examples/Scripts Ruff passes. Native, ordinary
  installed artifacts, release and private publication remain separate gates.

## 2026-11-12 — D46 documentation pass (Issue 250)

- Landed this session, all on `main`: float32 read-back tolerance in the native-driver payload comparison (`1c8e1ca`), the `install.vfpy` sync with the App installer (`535149a`, App `5cac0d6`, Issue 254).
- TODO row 21 now records the pens-floor diagnosis: `install.vfpy` enforces `fontlab-python-pens>=1.0.0` only on the `uv` route, while `install_siblings` and the no-uv `missing()` check skip the version. The fix is a feature change to the shared byte-identical `install.vfpy`, so it lands in App first and propagates; nothing is changed here. TODO adds the F47-1 and Issue 254 native checks, the licence verify-and-close row and a triage record: `668ec5d` (a `Path.is_dir` stub for `test_getgo_dir_when_no_candidate_then_returns_none`) is superseded by `990cb51` on main, which already isolates that test, and was not applied. PLAN drops a stale reconciliation line.
- WORK.md was already a short pointer and is unchanged. No code changed.

## 2026-11-12 — install.vfpy matches the App's installer, with Extensions bundle support (Issue 254)

- `install.vfpy` is now byte-identical to `fontlab-fontlabapp/install.vfpy` (pushed in App `5cac0d6`).
  The new code places `[tool.fontlab-install] extensions` bundles; this repository declares none, so
  installs behave as before. `tools/check_install_copies.py` in the App compares the copies by sha256.

## 2026-11-12 — Native-driver payload comparison tolerates float32 read-back (Issue 250)

- `tests/native_drivers/round10_payloads.py`: new `READBACK_ATOL = 1e-3` and `values_close` (structural comparison; numbers, including those inside node strings such as `"10.4 0 l"`, match within atol). `payload_equal` and `geometry_receipt.geometry_equal` now use it, so a Redo read-back of 10.3999996 for 10.4 no longer reads as a failure while 10.5 still does. Atol is App's measured `COORDINATE_TOLERANCE` (Redo drift about 1.6e-5, up to 5e-4 after save and reopen). Test: `tests/test_round14.py::test_values_close_when_float32_readback_then_equal_within_atol`.
- Still open: a live r31 rerun that uses the tolerance (TODO).

## 2026-11-12 — R39 kerning default-master targeting verified live (Issue 250)

- Livetester, Fontport `49520ce` with App e8a1209 (`reports/a2-live-report-47.md` part 1): with Light current (set by `setMaster` and by a UI layer switch), the write for master "Regular" landed on the default master Regular; Light and Bold were unchanged; Undo/Redo and save/reopen were exact.
- The all-masters fractional refusal appeared live and made no change: `Kerning on Light: L T = -26.5 is not a whole number; ... no changes applied.` After the UI layer switch (`r39u`), master="Regular" landed on Regular and Light was refused.
- Closed the R39 native rerun TODO row. Still open: writability and history of `kerning(<non-current master>)` (fl#8639, fl#8640).

## 2026-11-12 — Font kerning targets the default master and refuses fractions on every master (Issue 250, R39)

- `native_kerning.write_kerning` and `host.get_kerning` now address `flPackage.kerning(defaultMaster)` explicitly instead of the app-global current master (livetester R39, `reports/a2-live-report-39.md`: with Light current, a write for master "Regular" landed on Light). Packages without `defaultMaster` keep the old current-master call.
- `write_kerning` preflights every master: a fractional or non-finite pair on any master is refused before mutation as `Kerning on <master>: <left> <right> = <value> ...`, even when the staged edit equals the current kerning (native history rounds every master, so an edit on one could round another).
- `interchange.preflight_import`'s fractional-kerning refusal now names the pair and value.
- Tests: `tests/test_native_kerning.py` (default-master write/read, fraction and non-finite on a non-target master, no-op edit still refused), `tests/test_interchange.py`; suite 5119 passed, `native_kerning.py` 100% branch.
- Not proved live: whether `kerning(<non-current master>)` is writable with working Undo/Redo; the TODO rerun row stays open.

## 2026-11-12 — Pens suite in the Fontport pre-push gate confirmed (Issue 250)

- Closes the TODO row asking to confirm the pens suite in the Fontport gate. The real
  gate on 54ffe80 ran the Fontport suite (5110 passed) and then the pens suite
  (857 passed, 95.76%, 80% floor) with Suite exit 0 (`l2/gate4-fp.log`); the push
  ran the same hook, and CI on 54ffe80 succeeded.
- Float32 read-back tolerance (TODO and PLAN) corrected from 1e-4 to 1e-3, App's measured
  `COORDINATE_TOLERANCE`; the row stays open until Fontport has a read-back check.

## 2026-11-12 — Installer: unreachable blocked skip removed (Issue 250, review M-10)

- `install.vfpy` synced byte-identically from App (sha256 `2eb71691…` → `bbe8104e…`):
  `remove_old_dist` drops the `path.name in blocked` skip. Every blocked top-level
  name is also held, and a non-empty held refuses before anything is deleted, so the
  skip never ran. App's `tests/test_install_superseded.py` pins that invariant.

## 2026-11-12 — Fractional kerning refusal names the pair (Issue 250)

- `src/fontlab_fontport/native_kerning.py` `write_kerning`: the `kerning.fractionalHistory` refusal now reads `Kerning[ on <master>]: <left> <right> = <value> is not a whole number; native kerning history rounds fractional values. Round that pair first; no changes applied.` The master appears when the package exposes one.
- Two tests in `tests/test_native_kerning.py`; full Fontport suite 5112 passed, 2 skipped, `native_kerning.py` 100% branch. `interchange.py:181` is unchanged.

## 2026-11-11 — Record native pen rounding and float32 read-back as open rows (Issue 250)

- TODO.md: replaces the former row "Fontport pen writes to a native layer read back as integers" (old TODO.md:64, livetester report 29b) with two evidenced rows from reports 31/31e: pen writes round fractional coordinates in the fgShape-to-flShape `assign` (`src/fontlab_fontport/host.py:431`, `_stage_shapes`) under an app-wide "Round coordinates" state (fontlab/fl#8638), and float32 native read-back needing a 1e-4 tolerance on Redo checks. PLAN.md points at both. Documentation only; no source change and nothing is claimed fixed.

## 2026-11-11 — Lock refresh and pens suite in the pre-push gate (Issue 250, pens wiring)

- `uv lock` refresh against the current App metadata: adds the `uharfbuzz` test-extra requirement. `fontlab-python-pens` stays a path-editable source (workspace convention shared with App and Glyport, and what the live FontLab site-packages use); an editable lock entry cannot pin a version, so the released tags are recorded here: v1.0.0 to v1.0.2 are genuine tags, sibling checkout is v1.0.2 plus 5 commits (05792a4).
- The workspace gate recipe (`.metaswarm/repos.sh`, fontlab-fontport case) runs the pens suite (80% coverage floor) after the Fontport suite and fails on a pens failure; the pens editable install was already in the recipe.

## 2026-11-11 — get_info returns integral unitsPerEm/versionMajor/versionMinor as int (Issue 250)

- `NativeFontBackend.get_info` (`src/fontlab_fontport/host.py`) now converts integral floats to `int` for the `INTEGER_FIELDS` (`unitsPerEm`, `versionMajor`, `versionMinor`) as it already did for the eight vertical metrics. A fractional `unitsPerEm` (1000.5) and an existing int are returned unchanged. Tests: `tests/test_info_backend.py` (three new cases; the integral-float case failed first).
- Graph check: impact on `NativeFontBackend.get_info` returned 0 callers with risk UNKNOWN (dynamic dispatch), so it was confirmed by text search: callers are `export.py:81`, `interchange.py:56` and `live.py:221`. `graph.sh` against origin/main raised only code 5 (analyze truncation), which needs a reviewer ruling; detect reported 1 flow (Get_info → Normalize_info), risk medium.
- Source half only: the native readback of `unitsPerEm` on a live FontLab 9 font stays unverified (TODO row kept).

## 2026-11-11 — Memory-backend pen keeps fractional coordinates (Issue 250)

- `tests/test_round10_backend.py::test_pen_when_fractional_points_written_to_memory_backend_then_read_back_exactly` writes (10.4, 410.6), (100.25, 410.6), (10.4, 0.75) through `getPen()` inside `edit_glyph` and expects exact values both in the open glyph and in the committed `UFOBackend` glyph.
- Mutant: wrapping `memory.py:write_glyph`'s `source.drawPoints` in `RoundingPointPen` fails it. A first version reading only the cached glyph let that mutant survive and was replaced.
- Context: report 29b saw native pen writes read back as integers. Reading the Fontport/pens Python found no rounding; no cause is claimed. TODO has the livetester recheck (coordinate-rounding setting, pen vs flNode vs fgPoint). Native behavior is not established here.

## 2026-11-11 — APP_FLOOR strict/loose checks verified by mutants (Issue 250)

- Rechecked the closed row "Tighten the APP_FLOOR regex" (d651fb9, b097603) in `tests/test_issue122_t15_surface.py`. Loosening `APP_FLOOR` to `App\s*>=\s*` fails `test_app_floor_regex_when_text_is_loose_then_only_exact_floors_match` and `test_loose_detector_when_near_misses_then_strict_check_fails_them` (2 failed, 6 passed).
- Gap found and closed: removing the `(?<![\w-])` lookbehind survived every test. The loose-lookalike list now also has `my-fontlab-fontlabapp>=1.2.0` and `MyApp >= 1.2.0`, and that mutant now fails (1 failed, 7 passed). The real regex is unchanged; all 8 tests pass.

## 2026-11-11 — D18-2 vertical metrics verified live (A2 live report 21, Issue 250)

- Fontport 2255c2f on FontLab 9, read-only: all eight vertical-metric fields equal the raw native values for the current master (Typo 765/-235/200, hhea 965/-235/0, win 965/235); hhea integral floats come back as int. `italic_angle` stays float (0.0, -7.5, -12.0). Dialog comparison is owner-run.

## 2026-11-11 — Font Info vertical-metric gap recorded (A2 live report 18, Issue 250)

- Live on FontLab 9: the Font Info workflow passes (one Undo row, exact Undo/Redo, reopen), but `INFO_FIELDS` lacks eight vertical-metric fields. Recorded as an open TODO row (D18-2) with the patch named; nothing in this repository changes yet.

## 2026-11-11 — Native font info reads the eight vertical metrics (Issue 250, D18-2)

`NativeFontBackend.get_info` now answers `openTypeOS2TypoAscender/Descender/LineGap`, `openTypeHheaAscender/Descender/LineGap` and `openTypeOS2WinAscent/WinDescent` (new `READ_ONLY_FIELDS` in `src/fontlab_fontport/info.py`), which native `package.info` exposes but `INFO_FIELDS` lacked (livetester report 18). Integer-valued floats come back as `int` (UFO 3 stores these as integers); fractional values are kept. Read-side only: the fields are still refused by `set_info`, and UFO export is unchanged. Tests in `tests/test_info_backend.py` cover the integers, a fractional value, unknown-field refusal and write refusal; native readback of these fields on FontLab stays open in TODO. A further test pins the scope: an integral-float field outside the eight (italicAngle 0.0) stays a float; removing the `attr in READ_ONLY_FIELDS` guard fails it (49 passed in tests/test_info_backend.py, 1 failed with the mutant).

## 2026-11-11 — install.vfpy synced to the App WP11A installer (Issue 250)

- `install.vfpy` is now byte-identical to fontlab-fontlabapp 79f7485 (WP11A): it records file hashes in `install.log`, removes only superseded files whose current hash matches the logged hash, keeps edited ones and reports them, refuses entries with `..` or outside the data folder and any unowned entry in the old RECORD, and supports `FONTLAB_INSTALL_DRY_RUN`. Verify with `tools/check_install_copies.py` in the App repository. The native reinstall check is owner-run and stays open in the App TODO.

## 2026-11-11 — Live close() and empty-layer pen route verified (Issue 250 N3)

Live on FontLab 9809 with Fontport 5f35ae1 (A2 live report 16 part 2, evidence `r17_imp.json`, `r17_e_*.json`; the owner's D44 amendment allows scripts to save and close owned test fonts):

- `import_native` `close()`: inside the block one new document exists and all seven steps run (new, glyph, info, groups, kerning, lib, features; glyph `a` has 4 points). On exit the document is closed and the font list equals the list before. A held handle then raises `StaleObjectError: Font is closed`, and a second `close()` raises the same. No crash, 0.15 s. Closes the N3 TODO row.
- Empty-layer pen route: `edit_glyph("space", layer=Regular/Light/Bold)` writes two contours into each empty layer. Each write creates exactly one new element (shapes 0 to 1, no component) with exact points and the advance unchanged, as one row "A2 empty-layer". A full Undo walk returns to the empty start (dirty None), a full Redo equals the after-state, and save, close and reopen is equal with clean history. Closes the empty-layer TODO row.
- Observation: each write shows two Undo rows with one label (data row plus a no-op), the kept pre+post notify pattern; data is exact at every step.

## 2026-11-11 — Live import_native stem-snap chain verified (Issue 250 N3)

Live on FontLab 9809 with b0876c1 (lane l11fp, A2 reports 13 section 5 and 14 section 1; evidence `r13i_*.json`, `r14i_*.json`): the new owned document is active and clean when stems are written first; stems [88]/[44] survive the glyph, info, groups, kerning, lib and features steps; the stem write gets its own Undo row (the first content row, below glyph creation). Seven Undo triggers unwound the whole import to a clean document and seven Redos replayed it in exact reverse order, with Edit > Undo/Redo enabled throughout; an Undo of only the two later info rows left the stems unchanged. Each Fontport batch leaves a no-op checkpoint row (kept on purpose). Still open: the context manager's `close()` path.

## 2026-11-11 — App consumes capabilities() (Issue 250)

Fontport TODO row 48 is closed: App 8cc1264 (CHANGELOG entry "Font Info editor reads Fontport capabilities()") makes the Font Info editor take its blank-metric hint from `RFont.capabilities()["info.clearOptionalMetric"]`; App's other Fontport-feature refusals already surface as real `UnsupportedCapability` errors, and App keeps no Fontport handles that need `RFont.invalidate()` (its own `invalidate()` methods are UI refreshes, unrelated). App gate 12874 passed, 22 skipped.

## 2026-11-11 — Issue 250 N3: stem-snap info writes refuse unless the font is active and has no unsaved history

- `NativeFontBackend.set_info_many` (and `set_info`, `font.info` writes, UFO interchange) refuses a changing `postscriptStemSnapH`/`postscriptStemSnapV` with `UnsupportedCapability("info.postscriptStemSnap.history")` when the font is not the active document (`flWorkspace.currentPackage.fgId` differs) or `flPackage.getProperty("__has_history_changes")` is set. The whole batch is refused before any checkpoint, notify or write. Live FontLab 9.0.9809 evidence (A2 report 12): the native stem-snap setter disables Edit > Undo/Redo until the document is reactivated, and after earlier history it can leave the write unrecorded so a later Undo reverts it to an old snapshot while the document reports clean; a write to a non-active document got no Undo row and left the document reporting clean. Unchanged stem values and other fields are not probed; clean documents keep the D18 pre+post protocol. New `STEM_SNAP_FIELDS` in `info.py` and a named capability entry. Tests: `tests/test_stemsnap_history.py`; the `test_info_backend.py` fake package now models a clean document. Known gap (TODO): a history that was undone and then cleared also reads as clean, so it is not refused.
- Behaviour change for scripts: `font.info.postscriptStemSnapH`/`postscriptStemSnapV` assignments (and `set_info`/`set_info_many`) on a background font, meaning any font that is not the active document, now raise `UnsupportedCapability` instead of writing. The same assignment on the active font raises once that font has unsaved history. Activate the font and write stem snaps before other edits, or save first.
- Native UFO import (`import_native`, `ImportSession.begin` with `native=True`) now writes stem snaps first, before any glyph is created, while the fresh owned document has no history. Other info fields still follow the glyphs. Without this, any UFO with stem snaps would have failed the whole import, since glyph writes set `__has_history_changes`. Plain UFO imports keep the old order. Tests: `test_native_import_writes_stem_snaps_before_any_glyph_edit`, `test_ufo_import_keeps_stem_snaps_with_other_info_after_glyphs`. A live `import_native` check with a stemmed UFO is pending (TODO), including whether the new document is the active one when the stems are written.

## 2026-11-11 — Issue 250: pens v1.0.0 lock and recipe verified

- fontlab-python-pens v1.0.0 (and v1.0.1) are tagged. Fontport resolves pens as `{ path = "../fontlab-python-pens", editable = true }` (`pyproject.toml` `[tool.uv.sources]`), so `uv.lock` records the editable path and the pens entry needs no refresh. `uv lock --check` is not clean against current App main (11fd1d6): App's newer `test` extra adds `uharfbuzz>=0.39`, which is unrelated to pens. The pre-push gate runs with `--no-project` and does not read `uv.lock`, so the lock was not refreshed here. The workspace pre-push recipe (`.metaswarm/repos.sh`, `fontlab-fontport` case) already passes `--with-editable "$I/fontlab-python-pens"`. Nothing else to change; the installer-floor row (pens 0.1.0 in a FontLab site-packages) stays open because it needs the shared `install.vfpy` and a FontLab check.

## 2026-11-11 — Issue 250: native driver no longer requires Glyport sources

- `tests/native_drivers/driver_args.py`: Glyport's origin is recorded when its source resolves and skipped otherwise, since no driver phase imports it; `--require-glyport` restores the hard failure for runs that need the Glyport prerequisite explicit. Tests: `test_arguments_when_glyport_*` in `tests/test_native_driver.py`. The stale-module purge still names `fontlab_glyport` on purpose.
- Receipts record the check: the dry-run JSON and `result.json` both carry `glyport` (resolved origin, or `null` when skipped) and `glyport_required`, so a skipped check is never confused with a missing key. Tests: `test_driver_when_glyport_skipped_then_dry_run_and_result_json_record_it` plus assertions in the `arguments` and manifest tests. Gate 5082 passed, 1 skipped.

## 2026-11-11 — capabilities() after document close (Issue 250)

- `NativeFontBackend.capabilities()` no longer calls `_package()`, so `RFont.capabilities()` returns the static `NATIVE_CAPABILITIES` table after the FontLab document has been closed, as its docstring states. Live FontLab 9.0.9808 evidence (UI Cmd+W, Don't Save) raised `StaleObjectError("Font document has been closed")` before the fix. Test: `tests/test_host.py::test_capabilities_when_document_closed_then_returns_static_table` (external close and binding close; fails before the fix).

## 2026-11-10 — App feature_blocks native-import row closed (Issue 250)

The App's deferred `import_module("fontlab")` in `write_feature_blocks` is
unreachable on its own: the `NativeFontBackend` constructor (`__init__` -> `_package`) imports
`fontlab` first, so a missing host raises a plain `ModuleNotFoundError` there
before anything is written. Pinned by App
`tests/test_feature_blocks.py::test_write_when_fontlab_missing_then_backend_import_fails_first`.

## 2026-11-10 — Issue 250: own-menu lookup seam

- Own-menu lookup seam: now in fontlab-fontlabapp (`OwnedMenus.own_menu`) and used by Glyport. The register_menu failing-sync slot regression is `test_register_menu_when_sync_fails_in_callback_then_cleanup_is_deferred` in Glyport.

## 2026-11-10 — App floor regex tightened (Issue 250)

- `tests/test_issue122_t15_surface.py`: `APP_FLOOR` stays strict (`fontlab-fontlabapp>=X.Y.Z` and `App >= X.Y.Z` only). A new loose detector, `LOOSE_APP_FLOOR`, finds any `App` or `fontlab-fontlabapp` followed by a comparison and a digit; the doc check now fails when a doc has a loose hit the strict form does not accept, so near-misses such as `App>=1.1.0` or `fontlab-fontlabapp>=1.1.0.1` fail instead of being skipped. Tests pin the near-misses. `tests/test_package_boundaries.py::test_installer_when_read_then_app_floor_matches_fontlab_extra` now binds `[tool.fontlab-install].dependencies` to the `fontlab` extra's App requirement instead of a literal.

## 2026-11-10 — live font editing rule (Issue 250, D44)

- AGENTS.md: agents test and edit the font open in FontLab 9, starting from the Desktop VFJs, and may save them.

## 2026-11-10 — delivered lint-repair progress reconciled

The independently qualified 44-finding lint repair reached main `28864b509d5a67abc47ea20957f985175553b8ea`, sole parent `183a3c3f71367a59071b8c7befce3a98deefab4b`, through the unchanged installed hook: 5,075 tests passed, two existing optional skips; required Ruff has zero findings. Complete changed-module coverage is 92.857143% for feature_blocks and 100% for ufo_features, with zero exclusions under the unchanged 80% gate. [Exact-source CI](https://github.com/fontlabcom/fontlab-fontport/actions/runs/42836090070) passed both jobs with source and output SHA equal to that commit.

Remove only the stale pending lint-delivery requirement from PLAN/TODO. Keep whole-current-App/default resolution, final ordinary distributions, native/history/reopen, canonical adoption and publication checks open. The real hook qualifies current App only as a Fontport dependency boundary. Raw graph risk remains HIGH and nonexhaustive, with 90 omitted entry candidates, 66 skipped callees and three budget-cut walks; retain the bounded captured-cohort ruling and all native/private Pages holds. These are previously qualified results, not a new delivery or CI result for this guide proposal.

## 2026-11-10 — isolated graph guidance proposal

Prepare append-only AGENTS guidance for separate task-owned graph HOME and storage, ordinary-analysis scope and independently reviewed bounded recovery. Original guide and progress history remain intact; runtime code is unchanged. This candidate has no new test, integration, CI, native or publication result; independent review and delivery remain pending.

## 2026-11-10 — Exact current-main lint repair, source qualification

Resolved the44 required Ruff0.17.4 src/tests findings with annotation-only lazy callable exports, explicit truncating zip and test style/import cleanup. No runtime export binding, lint suppression/configuration or test-oracle change. Affected240 tests pass; full source5075 passed,2 existing optional skips,67 warnings. Combined source coverage91.39%; complete feature_blocks92.8571% and ufo_features100%, zero exclusions. Existing native/history/reopen, ordinary final artifact, current-App/default resolution, independent review and main-delivery gates remain separate.

## 2026-11-10 — P2 source/test review passed; integration gates remain

Qualified the new App recipe-workbench consumer against unchanged Fontport
production code, including the delivered filesystem-identity containment repair.

The independently reviewed fix closes in-flight close/nested-provider acquisition
and scheduling-failure retry defects. New real-Qt regressions cover complete
fractional reopened geometry and component conjugation across layers, font/glyph
guides and metadata/resources; connected Add/Start and captured-run stability;
active-window cancellation/isolation and the existing supervisor's actual
terminate/kill/terminal cleanup; and retained primary/cleanup errors with retry
only for unacknowledged owners. Shared helpers and worker policy are unchanged.

Final source checks passed: App 12,212 cases with no skips; Scriptmix 4,609 with
six unchanged skips; affected App 524; targeted Fontport 92; pinned Ruff on all
15 changed Python files. Complete workbench coverage is 187/202 statement-plus-
branch obligations (92.5743%); demo and menu each cover 7/7 (100%), all with zero
exclusions. Independent scoped specification/quality review passed F1–F3.
Retain the original close/reentry and queue REDs, the initial missing-shaping
runtime epoch and setup failures. The new font-guideline assertion correction
compares against independently transformed info while preserving all 107 other
info fields and the complete original test prefix.

These results close the implementation and source-test portions only. Post-change
graph, ledger/controller source qualification, genuine-commit documentation,
normal main integration and exact-commit CI remain open. No new commit, push,
ordinary installation, native result or publication is claimed. Source floor
eight, full parity zero, all 8,723 obligations and the minimum eighteen workflows
remain unchanged; ordinary artifacts/two prefixes/archives and native history,
Undo/Redo/reopen, literal U+2029, canonical adoption and private Pages holds remain
separate. Earlier history and its Scriptmix intermediate-file correction stand.


## 2026-11-10 — P1 containment round delivered; P2 remains next

The reviewed [P1 round commit](https://github.com/fontlabcom/fontlab-fontport/commit/0fe7712630487ddea8836cc0443b29983e9103d0)
reached main through the normal qualified pre-push gate (24 core passes and four
retained opt-in skips). Its [exact-commit Actions run](https://github.com/fontlabcom/fontlab-fontport/actions/runs/42802953892)
succeeded. Fontport's filesystem-identity containment fix and App regressions
resolved [issue 8624](https://github.com/Fontlab/fl/issues/8624), now closed with
[verified resolution evidence](https://github.com/Fontlab/fl/issues/8624#issuecomment-6765750168).
This completes the former P1 reproduction, source-review and main-delivery tasks;
it does not implement the P2 recipe-workbench composition.

Retained source gates are Fontport 5,076 passes plus one existing corpus skip,
271 affected App passes and 96.9231% complete batch-module combined coverage with
zero exclusions, including the unchanged covered 0.5-second startup check.
The commit-bound documentation gates passed three strict builds, 114 unit checks
and 14 legacy checks. All 524 rendered files match (App 54, Fontport 60,
Scriptmix 410). Fontport's [generated docs child](https://github.com/fontlabcom/fontlab-fontport/commit/c06b0b4d68dc11853e36e3b2e5db5daa8adae242)
is a direct child of its source commit and changes only two generated docs files.
Scriptmix's [public Pages run](https://github.com/fontlabcom/fontlab-python-scriptmix/actions/runs/42803269873)
succeeded; its unchanged 410 rendered files retain the earlier nine-route browser
proof. No new browser run or native qualification is claimed.

Correction to the earlier catalogue-intermediate shorthand: of 285 Scriptmix
Markdown intermediates, 14 match, 262 tracked files differ and nine generated
files are absent from the committed tree. The 271 differences are not all tracked
revision changes. The generator uses the last commit affecting the Scripts tree
(`git log -1 --format=%H -- Scripts`), currently
`09a09447df23d87373a8e4a3fa13381dc946d337`, not the whole source commit or a per-file
revision. The qualified publication is the 410 rendered files; this is not a
695-file parity claim or a waiver for missing generated intermediates.

P2 planning now targets actual recipe-only controls plus BatchPanel results,
with no implicit font or geometry preview. Source floor eight, full parity zero,
all 8,723 obligations and the minimum eighteen workflows remain unchanged.
Ordinary artifacts/two-prefix installation, native/history/reopen, U+2029,
archives, canonical adoption and other publication gates remain open.


## 2026-11-10 — filesystem-alias containment correction (Refs #8624)

Independent review found that the earlier source-tested containment candidate was not qualified: case and Unicode spelling aliases on the actual filesystem bypassed its lexical path comparison. Four real runner cases and four actual App boundary cases reproduced this defect in later-input and reversed order without writing inside the inputs. Those failures and the earlier timing failures remain evidence; the previous source-check entry is historical, not acceptance of the defective candidate.

The shared preflight retains its lexical fast path and also compares existing ancestor filesystem identities. It refuses case or Unicode aliases only when the filesystem identifies the same object; it does not fold names unconditionally. Missing/non-directory ancestor candidates preserve the previous per-item output-error behavior, while permission errors propagate before reservation. Existing validation order, duplicate/equality/no-overwrite policy and iterator release remain unchanged.

Current source checks pass: 5,076 Fontport tests with one existing corpus skip, 271 actual App boundary/shared-worker/deferred/lifecycle cases, unchanged covered 0.5-second startup oracle and both real nonblocking endpoint controls. All 24 original containment/control cases remain, with four filesystem-alias cases and one non-directory regression added; the App tests preserve the original three cases and add four aliases. Complete batch.py coverage is 96.9231% combined with zero excluded lines; pinned Ruff passes all three changed Python files. A fresh owned isolated child resolves the corrected source copy; older recorded source origins are preserved. Distinct-name branches exist for filesystems that distinguish these spellings, but this APFS execution does not establish cross-filesystem acceptance.

This is source/standalone Qt evidence for [Refs #8624](https://github.com/Fontlab/fl/issues/8624), not issue closure or native/ordinary-product acceptance. Independent scoped review/current graph and genuine commit-bound docs, fresh-main reconciliation, normal hooked delivery and exact-commit CI remain pending. P2, workflow17 qualification, artifact/two-prefix/history/reopen/canonical gates and source floor eight/full parity zero remain unchanged.


## 2026-11-10 — batch input containment source checks pass (Refs #8624)

The shared normalized-job preflight now rejects absent output UFOs below any resolved input, including later inputs and symlink aliases. Existing overwrite/equality/duplicate validation order and iterator-release behavior remain unchanged. The initial all-pairs implementation failed the retained 256-job start-time oracle; the same-symbol source-set/parent walk passes that unchanged oracle with coverage enabled. All failures remain evidence.

The dedicated eight-case RED preceded the fix. The final full Fontport suite passes 5,071 tests with one existing corpus skip, including all 24 new containment/control cases. The actual App boundary/shared worker/deferred/lifecycle cohort passes 267 tests, including both real nonblocking endpoint controls. Complete batch.py coverage is 96.5217% combined with zero excluded lines; pinned Ruff passes all three changed Python files. The isolated child resolves the actual changed helper from a genuine task-private editable source copy; this is source-cohort evidence, not full ordinary-product or native acceptance.

This closes the P1 source implementation/testing task for [Refs #8624](https://github.com/Fontlab/fl/issues/8624). Independent review/post-change graph, final documentation checks and normal reviewed main delivery remain before issue closure. The separate P2 workbench composition and all artifact/two-prefix/native/history/reopen/canonical gates remain open; source floor eight and full workflow parity zero are unchanged.

## 2026-11-10 — batch containment defect reproduced (Refs #8624)

Owned source-only probes reproduced eight missing eager refusals for destinations inside current, later or symlink-resolved input UFOs. Each unexpected iterator was closed without advancing; complete input trees and reopened models were preserved. Sixteen positive/refusal/release controls pass. [Issue #8624](https://github.com/Fontlab/fl/issues/8624) records the defect. The finite shared-helper repair and its source/full-suite/coverage/main-delivery qualification remain pending; this entry does not close the issue or qualify workflow17, ordinary distributions or native behavior.

## 2026-11-10 — reviewed main and documentation delivery verified

The additive [X2 source commit](https://github.com/fontlabcom/fontlab-fontport/commit/0a40367d302c2c7b46debf42f669b0a0ac2f2346) passed its genuine commit-bound strict documentation build and all 36 documentation unittest cases. Independent source/fix and graph reviews passed before normal push. The qualified installed pre-push gate passed 24 core tests with four existing opt-in skips. [Exact-X2 CI](https://github.com/fontlabcom/fontlab-fontport/actions/runs/42783608917) succeeded, and the direct [documentation-only successor](https://github.com/fontlabcom/fontlab-fontport/commit/eba61e032a9d8d71ac8dcb525ede3c4a31cf4749) preserved all non-docs source while delivering 60 generated files byte-for-byte equal to the commit-bound build.

Across App, Fontport and Scriptmix, all 524 delivered generated files match. Scriptmix's 271 differing tracked catalogue Markdown intermediates are historical source-link revisions: the build regenerates them as inputs and commits only rendered docs. This is not a claim that all 695 Scriptmix output/intermediate files match. The public Scriptmix Font UI Lab category and all eight new menu routes passed live checks, including immutable source links and source hashes. Private App/Fontport Pages operations remain held.

This closes the recorded X2 documentation, reviewed combined-main source, normal-push and exact-commit CI tasks. Earlier candidate and failure entries remain historical evidence. Source qualification remains eight workflows, full workflow parity zero, all 8,723 obligations and the minimum eighteen-workflow scope retained. Genuine archives/distributions/two ordinary prefixes, native/history/reopen, literal paragraph-separator editing, canonical adoption and remaining publication gates are not closed by this delivery.

## 2026-11-10 — Fontport documentation candidate corrected

Added the eleven missing current README lines to the authored index. Existing content and links are preserved; the complete README inclusion test is unchanged.

The strict build and 36 documentation unittest cases pass in owned full-history X1 copies with the admitted documentation-only overlay. Pinned Ruff 0.14.10 F/py313 passes all four changed docs test files. The earlier failures remain retained. All 42 production source hashes and their full-suite/coverage bindings remain unchanged.

This closes the candidate correction only. Independent fix review, post-change graph checks, an additive X2 commit and fresh X2 commit-bound documentation checks remain before normal hooked push and exact-commit CI. Generated-output promotion, full ordinary-product/native acceptance and private publication remain separate; source floor eight and zero full workflow parity are unchanged.

## 2026-11-10 — combined main-source verification

The reconciled App, Fontport and Scriptmix source passed the complete suites:
App 12,133 tests with no skips; Fontport 5,047 with one retained corpus skip;
Scriptmix 4,606 with six retained skips. The 42 complete changed production
modules reached 89.3023–100% combined coverage with zero excluded lines.
Pinned Ruff passed all 88 scoped Python files. Paired installed Plugmix consumers
passed 100 tests; the strict installed reader/lifecycle checks passed 31.

These results qualify the recorded source-test epoch only. They do not establish
full ordinary-product or native acceptance. Independent combined review, a main
commit, normal push and exact-commit remote CI remain pending. Tracked-change
graph analysis reports CRITICAL, HIGH and LOW risks; the separate staged graph
gate for 49 new paths remains pending. Documentation builds and generated-output
lineage remain separate delivery gates. Source floor eight, ten remaining source
workflows, zero full workflow parity and all 8,723 retained obligations are
unchanged. Existing ordinary/native and private-publication holds remain.

## 2026-11-10 — qualified source carried into main reconciliation

Feature Source and Proof (#10) is independently source-qualified, including
lossless supported UFO source, ordinary code view and safe refusals. Its retained
full suites passed App 10,377, Fontport 5,017 with one existing corpus skip, and
Scriptmix 4,583 with six existing skips. Detached Transform Preview (#15) is also
independently source-qualified; its retained full App run passed 10,544 and
Scriptmix passed 4,590 with six existing skips. The common final before-model
digest is included in the qualified #15 source fixture.

The minimum source floor is eight of eighteen; ten compositions still lack source,
full workflow parity remains zero and all 8,723 obligations remain. These are
retained source-epoch results, not tests of this new main union. Combined-source
tests, independent integration review, containing commits, exact-SHA remote CI,
matching ordinary artifacts, native/history/reopen and publication gates remain
open. Full literal-U+2029 editing remains pending; safe refusal is not successful
editing. Existing history below is preserved.


## 2026-11-09 — Exact feature source integration candidate

Preserve exact UFO feature source with a shared boundary scanner and checked structured staging; unchanged requests make no raw write. Keep ordered duplicate rows and leave native history parsing unchanged. Source qualification remains subject to independent review and complete controlled suites; ordinary and native acceptance are separate.

## 2026-11-07 — deferred staged image transaction

Stage actual PNG bytes and native image color/transform across fresh wrappers;
commit final glyph/resources together, including clear/replacement and metadata-only
rollback. Guard source identity/lifetime and expire staged handles on every exit.
Reuse existing native geometry dispatch without adding native resource support.

## 2026-11-07 — checked detached image resources

Read/write checked image PNG bytes through the real detached backend with atomic
resource/reference rollback, original binding lifetime checks and collision-safe
upstream naming. Preserve shared assets and parentless copies. Staged byte access
refuses explicitly until the immediate Task6c closure; native storage remains held.

## 2026-11-07 — detached image metadata preservation

Preserve all eight UFO image fields when loading checked live glyphs, staging
`edit_glyph` and writing UFOBackend glyphs, including real FontParts wrappers
and defcon image clearing.
Reuse upstream Image objects and retain existing image payloads and native refusals.

## 2026-11-10 — verified integration-round guidance

- Record current-main reconciliation in a new isolated successor, preservation
  of concurrent work and exact reviewed staging, combined repository/graph
  checks, independent merge review, required hooks and actual remote proof.
- Keep solved tasks in cumulative history and unfinished acceptance in the
  future queue. Native, installation, adoption, Issue 123 and private Pages
  boundaries remain unchanged. This entry records documentation only.

## 2026-11-10 — install.vfpy always reinstalls scripts and dependencies

- Every install copies all files from `Scripts/` afresh and replaces any file
  already at the same path. A symlinked script folder is replaced by a real
  folder; the link target is never written. A directory where a script file
  belongs is still refused.
- Required packages are installed on every run. Packages that no package
  index carries (the fontlab-* packages, pythonqtside) are installed from
  checkouts beside this one through their own `install.vfpy`, once per run
  and safe against cycles. uv receives every other requirement, so version
  ranges, markers and extras are enforced. Without uv, sibling checkouts are
  still installed and only the remaining missing requirements are reported.
- The installer is byte-identical across all eleven installer repositories.

## 2026-11-08 — Issue 241 write-back fixes

- UFO writes now copy anchors and guidelines from fontParts/defcon glyphs. `UFOBackend.write_glyph` called `dict()` on mark objects and raised `TypeError: 'RAnchor' object is not iterable`; it now copies name, x, y, color and identifier (plus angle for guidelines) explicitly. Regression tests cover both.
- Native glyph writes accept a contours-only edit on a layer with several shapes when exactly one untransformed, unshared, non-image shape holds contours. Only that shape is copied and rewritten; components, images and other shapes stay untouched. Transformed or shared contour shapes, contours over several shapes, adding contours where no shape holds them, component changes in the same edit, transformed layers, hinted layers and fractional anchors remain refused with errors that name the reason. Proof is offline host fakes only; native acceptance waits for the owner smoke steps in PLAN/TODO.

## 2026-11-07 — bounded native and ordinary-artifact qualification

Bounded owned-font native checks passed for explicit-master H reads across
Light, Regular and Bold and unhinted space/Regular replacement with an appended
triangle, exact readback and saved/reopened outline. H/Regular replacement is
still unsupported: the existing hinted-outline guard refused it and the saved
whole font remained unchanged. The successful unhinted case preserved sibling
semantics apart from the separately inventoried native timestamp side effects;
it does not qualify hinted replacement or whole-font history.

Ordinary precommit artifacts have matching source/sdist/wheel/site package
payloads in the normal 19-distribution cohort: App 620, Fontport 38 and Glyport
182 files; 2,011 installed RECORD entries were checked. These dirty-VCS
artifacts are separate from the bounded native runs. The consumer candidates
remain uncommitted; canonical adoption, clean committed artifact requalification
and delivery are not complete. Native notification can restamp 40 unrelated
glyph timestamps; the exact per-run date inventory remains explicit. No
whole-font history safety or general UI/workflow acceptance is claimed.

## 2026-11-07 — FontGate pens moved to fontlab-python-pens (Issue 235)

`fontlab_fontport.pens` is now a thin glyph-level adapter over
`fontlab_pens.fontgate`. `FontGatePointPen`, `draw_points`, `_draw_contour`,
`edit_geometry_ready` and `IncompleteContour` keep their names. Contours are
validated by the pens staging layer and written by its FontGate point pen into
`glyph.layer.shapes[0]` (inverse of layer × element matrices, as before); a
glyph without a layer keeps the native `createContour()` route. Components
stay glyph-level on `glyph.components`. Reading uses
`fontlab_pens.fontgate.draw_contour_points` per element, then components.
A `move` point after the first point of a contour is now refused. Offline
tests only; native FontLab writes remain unverified.

## 2026-11-05 — independently approved documentation applied

[Task 2 final review](../verification/issue-230/task-2-fix2-review.md) records
SPEC PASS / QUALITY APPROVED. The [78-file application receipt](../verification/issue-230/task-2-apply.json)
includes this repository's six guides and preserves all 21 repository heads,
branches, indexes and non-selected diffs. This is applied documentation evidence,
not a new product test, installed artifact, native result or publication.

The complete earlier handoff/history below retains its proposal-stage statements
and dated source pins. Later review, application and delivery status belong in the
[live workspace ledger](../verification/issue-230/progress.md). Original future,
native, artifact and preservation contracts remain binding.

## 2026-11-05 — documentation reconciliation proposal

Prepared repository-specific organization, test and MVP/delivery guidance from current source/test configuration and retained Issue 207–211 evidence. Distinguished current canonical layout from qualified candidates, future plugin ownership and unfinished native/artifact gates. Preserved all prior work and changelog evidence; no runtime completion, installation or publication is claimed. Completed historical task rows were removed from the active checklist and consolidated below from existing local CHANGELOG/WORK receipts. Unfinished native, artifact and integration checks remain open.

## Retained scoped completion receipts — corrected evidence map

These are dated results at the stated source/version and acceptance surface. They do not establish current integrated, installed, native or published acceptance. Full receipts and hashes are indexed in the workspace Issue 230 task-2 manifest. Canonical-preimage line ranges below refer to the unchanged historical documents, before these new entries.

- Issue205 editor/helper ownership reversal to App;6 lazy factories and boundary regressions.
  Historical receipt: CHANGELOG.md:50–65.

- Issue205 optional App dependency;Fontport backend/native drivers unchanged;isolated Fontport imports pass without App.
  Historical receipt: WORK.md:20–45.

- Issue205 ownership/dependencies/migration docs and boundary tests updated.
  Historical receipt: CHANGELOG.md:50–65.

- Issue205 full gates:Fontport4601+1skip;App7738;isolated App-free Fontport imports pass.
  Historical receipt: WORK.md:39–45.

- KerningEditor empty-input neutral prompt;half-typed pair still validates;source regression receipt.
  Historical receipt: CHANGELOG.md:205–213.

## 2026-11-05 — planning chronology reconciliation

Issue205 ownership/source and earlier provider-import history moved to recorded results; native UI/writer/history/UFO qualification stays open. Current99VFJ corpus paths and all1797upstream classification requirements remain live. Historical passing results retain their dated source and acceptance scope in the entries above and original history below. This documentation change creates no new runtime acceptance.

---
this_file: CHANGELOG.md
---

## 1.2.12 (2026-11-16)

- Move the Qt editors (`fontlab_fontport.ui.*`: info, groups, kerning,
  transform, batch, sequence) to `fontlabapp.fontui`. `fontlab_fontport.ui` is
  now one tombstone module whose attribute access raises
  `ImportError("fontlab_fontport.ui moved to fontlabapp.fontui")`. Delete it in
  the next release.
- Delete the expired `fontlab_fontport.vanilla` tombstone (VanillaSession lives in
  `fontlab_glyport.ui.session`) and `tests/test_vanilla_tombstone.py`.
- Move the UI tests and `examples/font_transform.py` to Fontlabapp.
- Add `designspace_io.export_designspace` / `write_designspace`: a `.designspace`
  plus one UFO per master (host-free tests; no native run yet). Add
  `Designspace.document`. Add `native_import.import_designspace` and
  `import_ufo_native` (native `open_font`; fake-tested). See verification/issue-201/task-17-report.md in the workspace.
- Export each master's own kerning: `ExportSession.master_kerning` is read through
  `NativeFontBackend.get_master_kerning(name)` (`flPackage.kerning(master_name)`),
  and `write_designspace` writes it to each master UFO. Groups, info, lib and
  features stay shared (key master). The `designspace.masterKerning` loss is
  narrowed to `designspace.masterData`.
- Delete `docs/ROUND10-NATIVE.md` .. `ROUND15-NATIVE.md` and the round-based
  `verification/` tree. Kept: `verification/issue-105/NATIVE-MANIFEST.json`
  (read by `tests/test_native_driver.py`; its dead `details` pointers to the
  deleted docs are removed) and `verification/issue-105/round10/{fontshell,memory}.jsonl`
  (the receipts that `tools/fontparts-coverage.py --reuse-parity` reads).
- Merged into the issue 205 layout (2026-11-04): the UI tombstone keeps issue
  205's per-name hints, `MOVED` sets and submodule finder; names that never
  existed stay `AttributeError`. `docs/ROUND10-NATIVE.md` .. `ROUND15-NATIVE.md`
  are kept with issue 205's edits; the round-based `verification/` evidence stays
  deleted.

## 2026-11-03 — Issue 205 final review

- Keep native edit-guard lookup below all module imports. Translate only missing
  `fontlabapp` modules into the `fontlab-fontport[fontlab]` installation hint;
  preserve unrelated missing-dependency exceptions.
- Require `fontlab-fontlabapp>=1.2.0` in the optional native integration and
  FontLab installer dependencies; align the documented minimum and regressions.

## 2026-11-03 — Issue 205 canonical module paths

- Use canonical App guard paths in native host integration, tests and docs.
- Retain the deprecated feature forwarder and UI tombstones, including their
  intentional legacy import tests and migration guidance.
- Reuse the reviewed path migration tool with boundary and idempotence tests.

## 2026-11-03 — issue 205: restore FontLab UI ownership to App

- Moved the ten FontParts editor modules and active-font feature helpers from
  Fontport to `fontlabapp.fontui`, with six lazy factories and their regressions.
- Restored `fontlabapp.core.scripting` feature helpers; the shipped Fontport feature
  path forwards lazily. Old Fontport UI imports raise precise migration errors.
- Removed App from Fontport base requirements; added Fontport's optional `fontlab`
  extra and App's optional `fontport` extra. AST tests enforce the allowed imports.
- Updated ownership, dependencies, examples and migration documentation.
- Verification and sandbox move limitation are recorded in WORK.md.

## 2026-11-03 — installer options, licence and cleanup

- `install.vfpy` reads optional `[tool.fontlab-install]` keys: `name` (the distribution
  record), `packages` (`[]` installs scripts only) and `dependencies` (what FontLab needs,
  instead of `project.dependencies`). Symlinks inside `Scripts/` are not copied.

## 2026-11-03 — install.vfpy fixes from runs inside FontLab 9

Verified by installing all nine packages inside FontLab 9 (Python 3.11.6, arm64).
- Dependencies with console scripts (glyphsLib, fontTools) failed: uv writes them to
  `site-packages/../../../bin`, which resolves through the venv link to the FontLab
  folder. `bin`, `share` and `include` there now link back into `.venv`.
- A failed install appends a `"failed"` record with the traceback and uv's output to
  `install.log`; List/Uninstall ignore failed records.
- Package records include `WHEEL`, so `uv pip check` accepts them.
- Scripts are copied file by file into FontLab's `Scripts` folder, from a package's
  `Scripts/` folder (exact case) and from folders listed in `[tool.fontlab-install] scripts`.
  Folders shared by several packages merge, e.g. two packages' `Scripts/Kerning`. The
  installer refuses to overwrite a file another package or the user put there; uninstall
  removes only its own files, their `.pyc`, and folders left empty. An older install's
  folder link (`Scripts/Aidus Code`) is replaced by copied files.
- `*.vfpyc` (FontLab's compiled `install.vfpy`) is ignored by Git.

## 2026-11-03 — install.vfpy creates FontLab's venv

FontLab's `python/3.11/site-packages` is now always a real folder; packages are
symlinked into it, so no `.pth` processing is needed. `install.vfpy` creates `.venv` with
uv from FontLab's exact Python version and processor type, and links the venv's
site-packages to FontLab's folder, so `uv pip install --python .venv/bin/python` installs
into FontLab. An older layout (FontLab's folder linked into `.venv`) is migrated.

## 2026-11-03 — reverse-domain extension id and install.log

`[tool.fontlab-install] id = "com.fontlab.fontport"` names this extension. `install.vfpy` keeps
`Extensions/com.fontlab.fontport/install.log` (JSON Lines; the last line lists every installed file),
puts copied code in `Extensions/com.fontlab.fontport/lib/`, and adds Scripts > Extensions >
List Extensions and Uninstall com.fontlab.fontport.

## 2026-11-03 — install.vfpy without uv

`install.vfpy` now needs only FontLab's Python. It asks FontLab for its data folder
(`flPreferences().dataPathDefault`), links a Git checkout or copies a plain folder into
`Extensions/`, and writes a `.pth` plus `.dist-info` into `python/3.11/site-packages`.
uv is used only to add missing dependencies. It never replaces folders it does not own.

## 2026-11-03 — release scripts

Added `build.sh` (uv build into dist/), `publish.sh` (`uv publish`; refuses a dirty
tree or an untagged HEAD) and `install.vfpy` (editable install into FontLab's venv
from inside FontLab). Version stays hatch-vcs from `vX.Y.Z` tags.

<!-- workspace-handoff:2026-11-03 -->
## 2026-11-03 — documentation handoff for November 2–3

Used as a provider in the recorded ordinary consumer cohorts; no new November 2–3 source delivery is attributed to this canonical checkout.

Provider participation does not establish new native editing/history/round-trip acceptance.

Observed canonical checkout: `main` at `cdf5200cc796`. No source integration is performed by this update.

Updated the requested AGENTS/TODO/PLAN/CHANGELOG/README documentation and
recorded the paused state. Existing project text, examples and history remain;
no runtime source, installation, native session, branch/ref, release or site was
changed by this documentation maintenance. Source/archive/ordinary/native and
promotion acceptance remain separate claims. Detailed workspace evidence is
recorded in the root CHANGELOG and retained verification reports.
<!-- /workspace-handoff -->

## Fontport full offline suite passes without skips — 2026-11-01

Full candidate suite with the current manifest-verified99VFJ corpus enabled and
ufo2ft installed:4844passed, zero failures/errors/skips,63upstream deprecation
warnings. All47source runtime files match the installed Fontport package bytes.
Corpus and manifest hashes remain unchanged after the full run. This closes the
previously skipped corpus/compiler checks for this exact offline environment.

Exact command, JUnit, runtime hashes and limits:
verification/issue-123/fontport-current-corpus-full-20261101.json. This remains
source-suite/owned-double evidence, not actual FontLab history or save/reopen.
No new distribution was needed for the test-only discovery repair; new packaged
test payload acceptance remains distinct. Native/cohort promotion, generated
reference and publication gates remain open; no live/canonical/corpus mutation.

## Fontport current GetGo feature corpus verified — 2026-11-01

Repaired test discovery to include packaged lessons/src/fontlab_python_lessons/
getgo/data while preserving legacy/override/nearest-ancestor behavior. Two new
layout cases failed before the repair. All9corpus/discovery checks now pass,
zero skips, against installed Fontport with fontlab imports explicitly blocked.

All99VFJs match the current manifest at revision
cf1319fa3c0c9f8c0703615231eabeab02cb5901;294713230bytes and manifest hashes
remain unchanged after checks. Features:85present/14absent;99identical no-op
writes return before native access,14missing-prefix changing writes are refused.
This closes the skipped offline corpus check, not real feature writes/history.

Evidence and exact commands: verification/issue-123/fontport-getgo-discovery-20261101.json.
Scoped syntax/import lint and diff checks pass. Only test discovery changed;
no runtime/corpus/native/canonical edits, new package build or publication.
Historical native receipts use earlier inputs and are not acceptance of this
current corpus revision. D29/D30 and whole-font native acceptance remain open.

# Changes

## 2026-11-10 — Issue 250 documentation round

- AGENTS.md describes the delegation, integration and release workflow.
- WORK.md reset to the current round; the earlier bytes are archived on the owner's workspace data volume, not public.

## 2026-11-01 — F1 I1 duplicate-owner refusal (source checkpoint)

- Require exactly one registered glyph name before resolving its record. Reject
  duplicate names in either order for reads and Unicode writes without exporting
  glyph data. Four regressions retain note/lib mirrors and refuse before history.
- Full source suite passes after repairing the baseline nested pytest.approx
  assertion: 4840 tests, 2 skips; changed-module coverage 83.26%. Native
  preservation, timing and artifact acceptance remain open.

## 2026-10-23 — Registered glyph Unicode access (source checkpoint)

- Read and assign Unicode values through the registered font's own glyph record,
  checking native font/glyph identity without exporting flGlyph.fgGlyph, which
  can drop a freshly set note's FontGate lib mirror. Retain native-global note
  handling, staging, true no-ops, history scope and notification order.
- Native-shaped regression controls exercise the measured destructive getter,
  noncurrent fonts with same-name/different-Unicode glyphs, empty/multiple scalar
  values and stale/missing/ambiguous records. Full source coverage, ordinary
  artifacts and actual repaired native read/write/history acceptance remain open.

## 2026-10-23 — Distribution portability and provenance

- Document a portable external scratch folder and explicit configuration-free uv
  source/artifact verification commands; retain the genuine App development floor.

## 2026-10-23 — Genuine App development contract

- Require `fontlab-fontlabapp>=0.2.26.dev150`, matching the audited genuine private
  candidate. Active development/setup instructions use ordinary resolution and
  clear version-fabrication variables. Native, cohort, release and lock refresh
  acceptance remain open; runtime and tracked lock bytes are unchanged.


## 2026-10-22 — Native glyph history scope

- Use App's shared canvas-history preflight before glyph history enrollment,
  auxiliary-layer addition/removal and new glyph creation. Preserve no-op and
  validation priority, lazy imports and detached conversion. Offline controls
  use the real shared guard; native acceptance remains pending.

## 2026-10-22 — Kerning editor opens with a prompt

- A fresh `KerningEditor` with both name fields empty now shows "Select a pair, or type the left and right names." instead of the key-validation error. A half-typed pair still shows the validation error.

## 2026-10-22 — Coverage tests for the UI editors

- Six `tests/test_cov_ui_*.py` files and the behavioural PythonQt fake `tests/_cov_qt.py` cover the batch, info, groups, kerning, sequence and transform editors and views (98-100% branch coverage). Tests only: no production code changed.

## 1.2.12 (2026-11-16)

- Keep the relocated App UI/feature helper provenance in NOTICE and both distribution formats; remove source process labels.

- `cdc7397`: recorded the offline test baseline.
- `3ec6e3f` and `2a73ebf`: moved the six FontParts-bound editors and their tests
  from App to Fontport. Generic lifetime, model and canvas helpers remain in App.
  The facade loads neither PythonQt nor editor modules until a factory is called.
- `57f00b1`: moved feature-block I/O from App, retaining active-font,
  source-snapshot and glyph-reference checks and master restoration.
- `35a08ba`: removed Vanilla implementation and tests from Fontport. The
  import-free migration error names `fontlab_glyport.ui.session`.
  Fontport has no runtime Glyport dependency; native driver source discovery
  still checks for Glyport sources.
- `c2e1d59`: changed the kerning view to use Fontport's sequence factory.
- `b085cf7`: made all six factory exports explicit, added attribute annotations
  and private helper docstrings, aligned the App dependency floor, and added
  five documentation/surface checks. Moved kerning tests use strict zips.
- Updated the module map, install ownership, licence, native limits and open
  acceptance work. Test setup now selects arm64 Python 3.11 and requires a
  fresh external cache to avoid stale App build versions. The project lock
  still lacks App and is not the canonical test environment.
- Earlier offline documentation/import checks passed in Python 3.11 x86_64:
  29 tests, exit 0; source/test lint also exited 0. These were offline checks,
  not arm64 host or native editor acceptance.

## v1.0.2 (2026-10-16)

Remove local absolute paths from docs/ROUND12-14-NATIVE.md (they shipped in the
v1.0.1 sdist; the wheel was clean). Found by the fontlabapp paired-artifacts
privacy gate.

## v1.0.1 (2026-10-16)

FontParts glue verified inside FontLab 9.0.9783 (issue 105): upstream fontParts
1.1.1 suite runs natively with every case passing or named (orphan 432 pass /
1,365 capability; attached 1,087 pass / 638 capability / 72 harness exclusions);
glyph writes undo with the first Undo (an extra empty Undo row is the named
capability glyph.exactSingleUndo); structured Panose / OS/2 weight and width /
stem snaps persist on the key master; public RFont.invalidate()/capabilities();
v1.0.0 editing contract kept by default, strict refusals opt-in (D18).

- Round 16: regenerate all native upstream ledger cells from C4 f3d7dc5 receipts,
  validating exact IDs, named classifications and aggregate counts. Refresh all
  RoboFab checklist boundaries and distinguish refused component replacement
  from successfully measured add/transform edits.

- Round 15 (driver only): compare empty notes and numeric values semantically,
  count glyph creation in package history, and exclude the named root edit/save
  timestamp while retaining raw evidence and strict outline/metric checks.

- Round 14: protect geometry Undo snapshots with copy-on-write working shapes;
  expose the measured extra no-op checkpoint as glyph.exactSingleUndo.
- Native receipts independently freeze/check MCP contour and component records,
  fail no-op geometry probes, and exercise both Undo/Redo rows separately.
- Name native multi-membership refusals, isolate the both-sided fixture, and
  expose key-master scope for Panose/weight/width/stem-snap capability routes.

- Round 13: mark cleared outlines/component transforms for native Undo; always
  close glyph mutation notifications in finally; probe glyph history containers.
- Compare empty shapes and layer UI selection semantically, round FlattenPen
  samples to integers, accept exported OS/2 numeric subclasses, name fractional
  UPM refusals and transfer large native replies in checked 8 KiB chunks.
- Refuse invalidation with provisional contours; warn on close before discarding
  them. Document key-master-only Panose/weight/width writes and C4 re-runs.

- Round 12: C4 ticket regressions for named dangling/unset/identifier/component
  refusals, integral-float UPM imports, QVariant lib arrays/reserved host keys,
  empty attached contour fixtures and provisional point-level editing.
- Route OS/2 Panose/weight/width through persisted master properties; refuse
  nonpersistent name-record changes before writes/history. Glyph edits now use
  pre/post notifications with one layer+glyph list, pending native re-verification.
- Separate reviewed attached-parent harness exclusions; repair hinted-name
  discovery, compare ControlBoundsPen to native boxes, activate/pass the owned
  fixture to examples, and fail unexpected example refusals.

- Round 11: public invalidate/capabilities; FontParts identity and tempLib;
  only named capabilities classify as exclusions; per-test fixture attribution.
  Native client wrapper uses checkout dependencies and ancestor workspace lookup;
  attached upstream mode, cached test map, bounded liveness checks, save/reopen
  sequencing, exact refusal/history receipts, and 19 owned examples.
- Breaking-if-enabled (D18): strict history/persistence refusals are opt-in.
  Default info edits and saves retain v1.0.0 behavior, including the native
  extra no-op info Undo row; untouched foreign baseline data does not block save.


- Round 10: real 1,797-ID FontParts yardstick and raw per-test receipts, with
  separate fontshell parity/live-font fixture routes and reviewed exclusions;
  owned native fixture and phased native controller; RoboFab checklist mapping.
- Persistent world register/unregister and caller-path launcher; 16 original
  owned-font examples; staged glyph pen edits and actual fontPens/Tools recipes.
- Incremental whole-UFO export/import staging, strict native preflight, field
  loss inventory and native per-glyph/VFJ receipts. Native multilayer import,
  guideline/image writes and other unsupported fields remain explicit refusals.
- Named StaleObjectError guards cached public glyph/child/font-data handles,
  external closure detection, safe world invalidation and failed-owner cleanup.
- Refuse new Unicode native glyph names before mutation; expose native event,
  precision/history/group-persistence capabilities and actual structured info
  setter routes. Unsafe native writes refuse before history. Extra info history and existing
  legacy-group save restrictions are opt-in under D18, not host-defect fixes.


## v1.0.0 (2026-10-16)

First tagged release: FontParts world on FontLab (fontParts.world, info, lib,
designspace, batch), Vanilla adapters, native feature-code read/write with a
simulation of FontLab's splitter, GetGo-tested (99 fonts). Issues 105, 108.

- Round-9 correction: restore no-op/explicit-language-system feature additions
  on feature-less fonts. Keep staging pure and check synthesis only on changing
  staged writes, never the Undo baseline. Match native CRLF/include scanning;
  verify all 99 GetGo identical writes and refuse only unsafe changing writes.

- Round-8 review: find GetGo through workspace ancestors or FONTPORT_GETGO_DIR;
  retain a single-line name table's unread final byte; clarify shared read/write
  validation and document tagless native over-read refusal. Refuse font-dependent
  implicit language-system synthesis before native writes; test all 14 naturally
  missing GetGo prefixes and add a recorded native refusal phase.

- Round-7 correction: replace the over-strict feature keyword guard with an
  exact native tokenizer/history-split simulation. Accept generated comments
  and aalt body references; check all 99 GetGo VFJs. Normalize textless VFJ slots
  explicitly and refuse changing writes that cannot preserve their tags in
  Undo. Record no-op/refusal failures with history/exception evidence.

- Round-6 review: retain feature arrays/classes/text and hashes on native
  readback mismatches, recording acceptance failures while continuing phases.
  Reject feature block headers/keywords that native whole-text history can
  split or re-key, including unsafe current Undo baselines; keep reads verbatim.

- Round-5 correction: read canonical native feature text through fontpr's VFJ
  serializer; write validated ordered prefix/tag blocks through native setters,
  with package/features history and feature-change notifications. Only arbitrary
  string splitting remains unsupported. Enable byte/class/Undo/VFJ native checks
  and isolated metadata timing; fix earliest partial-window teardown and receipt guards.

- Round-4 feature audit (its no-route conclusion is refuted/superseded above): expose precise UnsupportedCapability with
  checked API metadata; record unbound whole-text routines and lossy fragment
  limits. Add native API inventory/refusal and gated B08 Undo/persistence phases.
- Retain windows whose base constructor created a widget before raising; make
  post-VFJ foreign-lib differences non-aborting acceptance receipts. Document
  session-scoped ownership and the decision not to depend on typerig-lib.

- Round-3 review: strongly retain live Vanilla windows through deterministic
  signal teardown; preserve unchanged foreign lib leaves during nested edits;
  supply/check Glyport sources and imported origins; record foreign probes
  without aborting later phases; use in-host batch steps/native polls and normal
  event-loop deletion. Cleanup explicitly discards owned font edits and retains
  failed widget teardown state until the required test-host restart.
- Round-2 review: pin project Ruff rules and tested FontParts range; preserve
  foreign native lib entries and CR/CRLF with changed-value-only validation;
  use package/master history checkpoints; enforce absolute paths and eager
  batch reservations/case-insensitive destination checks; bound Panose to bytes;
  normalize structured readback; replace reused owned handles; reverse native
  design-to-user axis maps; release closed Vanilla windows. Split native checks
  into timed calls, add real B05/B10/external B09 drivers and ignored unique
  outputs. Correct the non-reproducible Round-1 Ruff claim.

- X3 host-free integration: add explicit FontWorld identity/ownership/refresh and
  temporary upstream world registration, optional VanillaSession over Glyport's
  existing Qt controls/dialogs, real FontParts features/lib wrappers and B08
  staging, native JSON-compatible packageLib routing, structured B05 fields,
  affine UFO recipes/transforms, designspace source/instance snapshots and
  bounded per-item batch execution. Native boundaries remain explicit.
- Add real saved/reopened UFO geometry, plist and feature-text tests; record
  upstream UFOReader CRLF normalization. Native whole-feature storage remains
  unavailable. Add owned GetGo native probe and complete Fontport manifest.

- Add pure `edit_groups` staging for explicit group creation, rename, deletion
  and deduplicated member insertion/removal. Require known glyphs for insertion
  and validate the complete result before any UI/native dispatch. A conflicting
  imported group can be removed to repair per-side overlap. No new dependency.

- Add real FontParts groups, explicit validated batch replacement and rename,
  separate native feature/key-master class storage and dependent-pair refusals.
  Preserve ordinary member order/duplicates, support empty native classes, and
  reject invalid membership before history. Native first Undo/Redo and VFJ
  reload pass for supported groups; other-master classes/pairs and glyphs remain
  unchanged. Native name restrictions, both-sided divergence and extra no-op
  history remain explicit; this does not complete B06 or its UI.

- PLAN/TODO reconciliation: moved the verified detached interchange/pen,
  live-state repair and immutable sequence-layout checkpoints out of future
  work. Evidence is recorded in the workspace issue105 acceptance audit:
  native UFO/VFJ persistence, installed wheel/sdist and scoped reviews. Expanded
  remaining native geometry, B05–B10, registration and final artifact gates;
  the complete environment remains unfinished.

- Add live font-information metrics, UPM and note support, with explicit
  `RInfo.apply(values, *, undo_name=...)` and native `set_info_many` batching.
  Reject the entire batch before mutation for invalid values or unknown fields;
  preserve glyph geometry on UPM changes. Native first Undo/Redo and saved VFJ
  reload are verified; required pre-edit history checkpoints add a no-op row.
  Native optional metrics cannot represent unset values; `None` is refused.

- Add read-only text and slash-name sequence placement using fontTools kerning
  lookup, stable occurrence identities, left/right direction and explicit
  missing-glyph entries. Validate finite metrics/kerning and accumulated
  positions. No shaping or sequence UI is claimed.

- Add real FontParts font/layer/info objects with defcon glyph change forwarding,
  explicit refresh, stale-handle refusal and rollback on rejected writes.
- Expose native default-layer glyph order and declare the directly used defcon
  dependency. The bounded registered-document backend and complete environment
  acceptance are tracked separately from detached interchange.

- Begin issue 105 with real upstream dependencies and lazy native imports.
- Add point-pen interoperability preserving curve degree, point names and
  smooth flags; validate contour input before native creation.
- Cover open/closed and implied quadratic contours, empty contours and
  fontPens segment output. Native fixture verifies a FontGate point roundtrip.
- Read every selected-layer shape with its transform and invert the working
  shape transform for incoming glyph coordinates.
- Convert native glyphs to detached upstream FontParts/ufoLib2 objects and
  stage explicit glyph writes, retaining target names and other layers.
- Preserve nested plist metadata, binary data and XML text through the native
  typed string map, bypassing three legacy binding defects demonstrated by
  native fixtures. Keep the native reserved note field explicit.

The live FontParts backend and UI integrations remain in development.

## 2026-10-15 — B07 explicit kerning checkpoint

- Add actual BaseKerning mapping, complete validated batches and upstream
  fontTools effective fallback. Preserve explicit zero versus absence.
- Add key-master native typed-name routing; retain zero pairs across every
  glyph/group form, first Undo/Redo, native effective cache and VFJ reopening.
- Refuse native fractional history and values outside signed32-bit range before
  mutation; the host's Redo rounds fractions. Installed artifact/UI gates remain.

- Issue120 candidate: App owns generic VanillaSession lifetime; Fontport keeps an identical-class compatibility import. Existing optional Glyport factories and cleanup behavior are preserved. Native/release acceptance remains pending.


## 2026-11-01 — Restore coordinate assertion under current pytest

The unchanged HEAD pen test reproduces nested pytest.approx TypeError under
pytest9.2.0. Compare each ordered point separately, with explicit count and strict
zip; preserve default coordinate tolerance. Independent scoped review approves.
Official contract: https://docs.pytest.org/en/stable/reference/reference.html#pytest-approx
From this checkout, `rtk proxy /opt/homebrew/bin/python3.11 ../checks/run.py python -B -m pytest -p no:cacheprovider -q`
now exits0:4840passed/2skipped/63existing warnings. Log:
../checks/i1-full-pens-fixed-20261101.log. Scoped Ruff and git diff --check exit0.
No runtime pen change, dependency pin, native verification or promotion.

## 2026-11-01 — Consolidate the final candidate

Merged the retained candidate into the consolidated branch, preserving the newer
branch changes. Verification from the workspace root:
`rtk proxy sh .metaswarm/quality.sh coverage "$CHECKOUT" fontlab-fontport`
(`CHECKOUT` is this isolated checkout): 4,843 passed, one optional test skipped; exit 0.
No native FontLab operation was run.

## 2026-11-06 — Private source/build documentation candidate

Added five core website pages and all eleven maintained source guides, preserving the complete 1,797-row FontParts ledger and native provenance. Updated only active documentation-path consumers and packaging selection; the migration tool follows authored Markdown while leaving generated output alone. Added ordinary fixture/error/CLI coverage and a separate hash-locked every-main source/output build workflow. Runtime package bodies, dependencies and native acceptance are unchanged; private Pages operations remain held.


## 2026-11-07 — Exact frontend notices and English search assets

Added exact upstream frontend notices and source-map provenance for the existing MaterialX 10.1.8 payload. Explicit English configuration and a small build hook reject language, corpus, reference, asset-set or hash drift before omitting the 35 unused language helpers. All nine retained core assets, original product legal files, guides, catalogue rows, media, runtime and dependency/build locks are preserved.

The strict site build and all 35 documentation tests pass. The complete new hook has 100% statement/branch coverage; real Git staging, checkout and archives preserve exact legal bytes. An independently installed matching lock reproduces all 60 output bytes and modes. Existing immutable source/output, epoch, concurrency and full-parity workflow checks remain active. Browser and independent review evidence are separate from these local checks.

Private Pages configuration, grants, requests and publication remain owner-held; this source follow-up adds none.
No product release or installation is claimed. Prior ordinary artifacts remain bound to their recorded revisions; a later Git revision changes genuine hatch-vcs metadata. Full current source archives include these documentation additions; no unchanged-sdist or whole-wheel identity is asserted. Native acceptance and owner installation remain separate.


## 2026-11-07 — installed icon path-tuple inventory refinement

The current HTML/CSS contains 45 distinct ordered SVG path tuples. A complete scan of the four installed MaterialX icon families finds 43 exact installed matches and two unmatched Lucide tuples, refining the earlier known-candidate inventory. The additional installed match is the Font Awesome version caret-down. Its existing CSS header and full notice retain Font Awesome Free 7.1.0, Fonticons and CC-BY-4.0 icon attribution. The official NPM caret SVG has different raw path bytes; no unmodified-primary SVG, whole-geometry or optimizer-recipe equivalence is claimed. The two unmatched Lucide tuples retain their pinned SCSS source attribution.

A new actual-output regression derives these counts and checks installed matches, unmatched CSS references and the caret header. It fails against the prior 42 count and passes with the corrected metadata. All 36 current documentation tests pass; full strict and independent exact-lock builds match every output byte and mode. Only the legal paragraph, corresponding inventory and legal search row change in the site. Runtime, packaging, generators, vendor assets, full notices, existing guidance and the Fly search fix remain exact. Fresh browser verification and independent review are recorded separately. No private Pages operation, delivery, installed-product upgrade or native acceptance is claimed.

## 2026-11-09 — Issue 242 shared-pens main candidate

Fontport pen protocols delegate to fontlab-python-pens (Issue 235 commit d4b7d1a, cherry-picked onto the Issue 241 write-back fixes). `host.py` keeps calling `_draw_contour(contour, pen)`, which now aliases `fontlab_pens.fontgate.draw_contour_points`. The dependency floor is `fontlab-python-pens>=1.0.0`; `uv.lock` is refreshed. Source tests only: 4,667 passed, 2 skipped; `pens.py` 100% covered. No native acceptance is claimed.

## 2026-11-09 — Issue 242 review fixes: public pens API only

- `fontlab_fontport.pens.FontGatePointPen` now subclasses the public `fontlab_pens.StagingPointPen` and runs its initialiser. Each validated contour is written by a `fontlab_pens.fontgate.FontGatePointPen` built with an explicit `kind="layer"` or `kind="element"`, so Fontport no longer bypasses pens' constructor or imports private pens names (`_native`, `_NATIVE_KIND`, `_append_contour`, `_check_component`). It uses `StagingPointPen`, `StagedPoint`, `invert_transform`, `staged_node_kinds`, `FONTGATE_NODE_TYPES` and `StagingPointPen.check_component`. A source test rejects private pens imports.
- Names no longer re-exported by `fontlab_fontport.pens` since the pens delegation: `PointToSegmentPen`, `RecordingPen`, `TransformPointPen`, `Identity` and `_inverse_transform`. Import the first four from `fontlab_pens`; `fontlab_pens.invert_transform` replaces `_inverse_transform`. The module's public `__all__` (`FontGatePointPen`, `IncompleteContour`, `draw_points`, `edit_geometry_ready`) is unchanged.
- Changed empty-layer route: when `glyph.layer` exists but has no elements, the first contour now appends one new `fgShape` to `layer.shapes` (later contours go into that element). Before the delegation this case called `glyph.createContour()`. A glyph with no layer still uses `glyph.createContour()`. The new route is proven by offline doubles only; native verification is a TODO.
- `fontlab_pens.PenError` now subclasses `fontTools.pens.basePen.PenError` when fontTools is importable, so either `except` clause catches pen errors.
- `test.sh` exits 2 with a message when the sibling `../fontlab-python-pens` checkout is missing.

## 2026-11-10 — categorized package demos

- Add three functional Scripts-menu demos using detached package data and existing functional category names.
- Include Scripts in source distributions; document optional Fly/App snapshot reporting and host-free result access.
- Add real API result, menu wiring and report-failure tests. Native UI acceptance is separate from offline execution.

## 2026-11-10 — concurrent main reconciliation

Reapply the reviewed package demos on the newer main containing the shared-installer update and the independently corrected GetGo negative fixture. Preserve incoming installer/generated documentation and both rounds of agent guidance. Retain the upstream fixture correction rather than duplicate the local test-only repair; real corpus validation and its oracle remain unchanged. The earlier local gate passed, but remote delivery was rejected after main advanced; qualification of this combined source remains separate.

Mirror the demo README paragraph in the authored documentation index, preserving the complete README/index contract. The source-navigation link targets GitHub main; it makes no immutable-provenance claim. Strict build output is checked separately; incoming generated docs are retained until the qualified CI rebuild.
