---
this_file: AGENTS.md
---

## Owner priority: functional progress first (2026-11-15)

Future agents must make large, swift advances in working functionality. Prioritize visible user problems and useful, coherent feature increments. This instruction sets the work order and supersedes older requirements to complete exhaustive testing or build test infrastructure before ordinary implementation.

Keep packages coherent and compatible. Check shared APIs, imports and lazy aliases, data formats, dependency direction, object ownership and lifetime, installers, launchers and examples. Update affected providers and consumers together; preserve existing supported behavior and avoid dependency cycles.

During implementation, use the smallest meaningful smoke checks and focused regression tests for the changed behavior and affected package boundaries. Detailed testing, exhaustive coverage, broad performance studies and full acceptance matrices can follow in a later testing pass. Do not let test harnesses, sandbox/supervisor design, repeated unchanged suites, evidence machinery or review paperwork become the main project. Build such infrastructure only when a concrete functional defect or necessary safety constraint requires it.

Record deferred checks and known limits plainly. Do not call untested native, installed or published behavior verified. Keep existing mandatory delivery hooks, preservation rules, licence/privacy obligations, repository exclusions and explicit native/publication holds intact. When one action is held, continue other authorized functional work instead of expanding unrelated infrastructure.

Choose the next substantial useful feature or shared fix and carry its affected providers and consumers together. Timebox supporting investigation; once focused checks establish a usable increment, continue functionality work. Queue detailed testing for a later pass with its concrete remaining checks instead of letting test infrastructure displace product delivery.

## Current scope — 2026-11-05

Issue 230 documentation reconciliation is current. Issue 123 remains paused. The qualified Issue 207 isolated candidate is separate from canonical source, installed artifacts, native acceptance and publication. Reconcile that candidate with later work before integration. Issue 210 specifies future architecture; Issue 211 retains unfinished follow-up checks. Retained dated receipts describe their original source and acceptance surface only.

Canonical source inspected for this proposal: `998d59313ea7`. This is a dated source observation, not an installed or native acceptance claim.

Reconcile the Issue 207 candidate with the current DesignSpace/UFO/fontParts boundary; preserve all host data and origin guards.

Qualify native object lifetime, full-font history, Undo/Redo, failure paths and saved/reopened artifacts through matching installed consumers.

## Organization and checks

`src/` contains the public package and native adapters; `tests/` has offline contracts; `native-drivers/`, `examples/` and `src_docs/md/guides/` hold owned-host drivers and usage. FontLab UI editors belong in App.

Use the explicit arm64 Python 3.11 `fontport_check` recipe in README, with a matching App checkout. `./test.sh` accepts `FONTLABAPP_DIR`, otherwise uses sibling App, and runs pytest with defcon, fontParts, fontPens, fontTools and ufoLib2.

# Fontport rules

Bridge FontLab to real FontParts objects and UFO data without replacing upstream namespaces.

## Ownership

- Fontport owns DesignSpace/UFO/fontParts adapters, including the FontLab backend and the DesignSpace export/import wrappers. It has no UI (issue 201).
- FontLab editors and active-font feature helpers belong in `fontlabapp.fontui`.
- General UI and shared script helpers go in `fontlabapp`; Glyphs.app compatibility goes in `fontlab_glyport`.
- Scripts access App through `fly`. Fontport internals use relative imports for Fontport code, lazy optional `fontlabapp.core.edit_guards` imports in host.py, and `fontlabapp.fontui.feature_blocks` in the deprecated feature forwarder.
- Vanilla lives in `fontlab_glyport.ui.session`; `fontlab_fontport.vanilla` is deleted.
- Keep native and Qt imports lazy. `fontlab_fontport.ui` is a one-release `ImportError` tombstone pointing to `fontlabapp.fontui`: delete it in the next release. Add no UI here.

## Commands

Host work requires Python 3.11 arm64. A generic 3.11 selector can choose x86_64.
From this checkout, prepare the shell below. It needs uv, network access,
an arm64 Python installation or permission for uv to download one, a sibling
App checkout with the required UI helpers, and a fresh writable external cache.
App must meet `fontlab-fontlabapp>=1.2.0`; do not fabricate its version.
Both editable packages are installed only in the external test environment.

```sh
: "${FONTLAB_SCRATCH:?Set FONTLAB_SCRATCH to a writable external-drive folder}"
mkdir -p "$FONTLAB_SCRATCH/tmp" || exit 1
export TMPDIR="$FONTLAB_SCRATCH/tmp" UV_CACHE_DIR
UV_CACHE_DIR="$(mktemp -d "$TMPDIR/fontport-cache.XXXXXX")" || exit 1
for scm_name in $(env | sed -n 's/^\(SETUPTOOLS_SCM_PRETEND_VERSION[^=]*\)=.*/\1/p'); do unset "$scm_name"; done
export PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export PYTHONPATH=src:../fontlab-fontlabapp/src:../fontlab-fly/src
fontport_check() {
  uv run --no-config --python cpython-3.11-macos-aarch64-none --no-project \
    --with pytest --with pytest-cov --with ruff --with defcon \
    --with "fontParts>=1.1.1,<1.2" --with fontPens --with fontTools --with ufoLib2 \
    --with-editable ../fontlab-fontlabapp --with-editable ../fontlab-python-pens \
    --with-editable . "$@"
}
fontport_check python -B -m pytest -p no:cacheprovider -q
fontport_check python -B -m pytest -p no:cacheprovider -q -k 'readme or docs_when_app_floor'
fontport_check ruff check --no-cache src tests
```

`uv.lock` has no App entry; the project test launcher is not the canonical gate.
Batch tests need installed Fontport because their child uses `python -I`.
Optional font compilation tests also need ufo2ft in the external environment.

## Host limits

- Use FontLab's PythonQt and existing application loop. Widgets are in `PythonQt.QtGui`; `QObject` is in `PythonQt.private`. Do not load PySide/PyQt or create a QApplication.
- Keep editor handles alive; disconnect owned signals before deferred deletion. Put Python state on Python owners, not native widget instances. Call native protected event handlers explicitly instead of `super()`.
- A Python exception during painting can crash FontLab. End an active painter in `finally`.
- Never read `fgPackage` from an unregistered `flPackage`. Do not add bare `fgGlyph` objects to a package before MCP kerning calls; both paths have crashed the host.
- Use absolute host file paths. MCP save writes a copy and retains dirty state/source paths. Read `__has_history_changes`, not the widget modified flag.
- History notifications need the layer and glyph in one list. Preserve the measured extra checkpoint; do not claim one-row Undo.
- Native shape clones can change raw node flags and lose shape notes. VFJ reload can change node types. Compare topology and unrelated data after Apply, Undo, Redo and reopen.
- Native anchors round fractions; kerning Redo rounds fractions. Keep explicit refusals. Moving an existing anchor to the origin also needs separate Redo proof.
- Do not notify automatic layers or hide unrelated timestamp changes from queued updates. Metadata scans through `flGlyph.fgGlyph` can clear the FontGate note mirror.
- `run_python` has a fixed five-second deadline; client timeout does not cancel host work. Split long work and enforce deadlines inside FontLab.

## Native proof and file safety

- Offline tests, import checks and old receipts are not new native proof. Test installed artifacts on owned fixtures in a dedicated document-free FontLab session; restart after each mutating suite.
- Owner-managed editable installs can shadow this checkout. With no live handles, purge stale modules, put this `src` first, and assert import origins before native checks.
- Never install into or uninstall from FontLab's site-packages. Never mutate borrowed user documents or close a font while its Save Changes dialog is open.
- Work only in the authorized worktree. Preserve owner edits and sealed evidence. No stash, reset, clean, checkout switches, merges, pushes or commits without task authorization.
- Read-only Git: `GIT_OPTIONAL_LOCKS=0 /opt/homebrew/bin/git --no-optional-locks …`.

## Milestones and delivery

Read [PLAN.md](PLAN.md), [TODO.md](TODO.md) and [WORK.md](WORK.md) before work.
Make the smallest complete MVP for one named acceptance task. Find all callers,
tests, fixtures, exports and documentation first. Use graph impact before source
symbol edits; confirm stale or unknown graph results against current source.
Keep product work in isolated successors and preserve the owner's checkout.

Run this repository's exact checks and the unchanged 80% gate for each complete
changed production module. Use an independent review before a milestone commit.
Under the current owner task, commit and push reviewed, passing milestones;
verify remote heads rather than inferring delivery from local tracking refs.
Before main integration, reconcile concurrent work and all consumers, run graph
change analysis and repeat the required acceptance on the combined source.

Before removing obsolete branches or files, prove integration, retain recoverable
unique work and check fresh owner/worktree attachments. Preserve sealed reports,
licences, archives and private data. Do not rewrite history by implication.
Remove verified completed work from PLAN/TODO and record scoped evidence in
CHANGELOG. Keep implemented-only native/artifact checks open in TODO. Issue 123
remains paused; no instruction here authorizes driving the owner's FontLab,
installing into its user folder or publishing a site.

## Source/build-only documentation

Authored public guides live in `src_docs/md/guides`; five core pages provide website navigation. The site uses fly-january 0.4.0 or later (remote theme assets) with FontLab chrome. Install `src_docs/requirements.txt` with `--require-hashes` in the separate Python 3.13 environment. Run `sh src_docs/build.sh` and `python -m unittest discover -s tests_docs -v`. Generated `docs` is immutable output. The every-main workflow verifies source/output lineage, a shared source epoch and complete tracked plus ignored/untracked parity. All twelve private P/L holds remain; no Pages grant, helper or request belongs here. Preserve native/owner-install gates.

## Integration rounds

After each round of important changes, integrate it into `main` and upstream:
fetch `origin/main`, build the change on top of it in an isolated branch or
worktree, and resolve conflicts by keeping both our work and teammates' work.
Never discard upstream commits, and never force-push. Run the repository's
checks on the merged result, then push to `origin main`. Record the change in
CHANGELOG.md, move verified-solved TODO.md items into CHANGELOG.md, update
PLAN.md, and continue with the next TODO.md item until the list is clear.
`install.vfpy` is shared: keep it byte-identical in every installer repository.

## Owner workflow — 2026-11-10

After each important round, reconcile current team work and integrate independently reviewed, verified changes into main using the repository's delivery gates. Preserve owner branches, indexes and unrelated work. Move only verified solved TODO items into cumulative CHANGELOG, update PLAN for remaining work, and continue the authorized backlog. Keep unverified native checks and owner-paused tasks open; this workflow does not authorize installation or bypass preservation gates.

## Verified integration rounds — 2026-11-10

After each important independently reviewed round, recheck actual upstream
`main` and owner/worktree attachments. Fetch in a new isolated successor based
on current `origin/main`, merge the round's reviewed work, and resolve conflicts
by preserving both sides' intent, newer fixes and teammates' changes. Preserve
owner checkouts, branches, indexes, refs and configuration; never pull, switch
or rebase an owner's or another agent's active worktree. Stage only the exact
reviewed residual delta. Run the repository's applicable full suite, lint and
graph change gates on the combined tree, obtain independent merge review, then
commit and push under the current owner task's authority. Keep required hooks,
including the installed Dismisser pre-push gate, active; never bypass them or
force-push or rewrite history. Verify the actual remote head and required
main-triggered Actions; a local tracking ref is not delivery proof.

Move only evidenced solved tasks from future PLAN/TODO into cumulative
CHANGELOG, retaining every unrelated entry and placing new progress first. Keep
TODO flat and unchecked, update PLAN to remaining work, and continue the next
authorized task. Unverified native, SDK, UI, history, artifact, adoption and
publication checks stay open. The workspace root remains non-Git. Preserve
excluded repositories, recovery, licences and private data; this workflow does
not authorize FontLab installation or native operations, resume Issue 123, or
lift private Pages holds. Native upstream fixes use reviewed PRs to the
cause-appropriate Proteus, FontGate or pyfontgate repository.

## Isolated successors

Overrides generic bootstrap/MCP.

For graph work in an isolated successor, use the qualified installed CLI or backend with both `GITNEXUS_HOME` and `GITNEXUS_STORAGE_PATH` set to separate task-owned locations before the first invocation, including index discovery and analysis. A private storage path alone can still register the successor in global control files. During ordinary analysis, do not fall back to global MCP defaults, global `list-repos` or global setup/bootstrap, and do not make unreviewed global registry edits. Retain exact command/selected environment and before/after owned metadata; record expected task-owned `.git/info/exclude` additions and preserve unrelated state. If discovery or indexing escapes the owned scope, preserve evidence and obtain independent bounded control-file review before integration. Any necessary recovery must be separately reviewed, use fresh guarded current bytes and reviewed writer coordination, and change only the proven task-owned entry while preserving all other current records and bytes; never restore an old whole global registry.

## Agent workflow (Issue 250, 2026-11-10)

- Plan with `superpowers:subagent-driven-development`: one fresh implementer per task, a separate read-only reviewer, then the controller runs the gates and commits.
- Send bulk, well-specified work to Codex via the `codex-delegate` skill (`node ~/.agents/skills/codex-delegate/scripts/relay.mjs --brief BRIEF --cd WORKTREE`, in the background). Use `claude-delegate` or `cursor-delegate` for second opinions or independent lanes. Delegates never commit, push or tag.
- Work in a fresh worktree of `origin/main` on the workspace data volume; never pull, switch or reset the owner checkout. Merge `origin/main` again before pushing, keep both sides' CHANGELOG/PLAN/TODO entries, rerun the full suite, lint and graph change analysis, push through the pre-push hook where one is installed (never force), verify the remote SHA and the CI run where a workflow is configured. Held private Pages operations (workspace D41) stay held.
- Release: tag the next semver above the latest tag and publish a GitHub release. Install released, gated packages into `~/Library/Application Support/FontLab/FontLab 9/` and test live in FontLab 9. This owner route (Issue 250) supersedes, for released packages only, every older line in this guide that forbids installing into the FontLab user folder or its site-packages, owner-managed editable installs, or starting FontLab for a live test (the owner's canonical editable checkouts themselves stay owner-managed): record the previous installed distribution first so it can be restored, and never touch FontLab preferences (owner fonts and documents: see live font editing below); native work goes through the workspace `verification/issue-104/fl-native.sh` gate.
- Documents: CHANGELOG holds verified completed work; TODO only open or to-verify items; PLAN the major remaining changes; WORK.md the current round only (older WORK bytes are archived on the owner's workspace data volume, not public).
- Native defects: issues at github.com/fontlab/fl; fixes as pull requests to fontlab/Proteus, fontlab/FontGate or fontlab/pyfontgate. Never commit to the local C++ snapshot.
- Older "work directly" or "no delegation" lines in this guide are superseded by this section (Issue 250).
- Live font editing (owner, 2026-11-10; workspace D44): test, verify and edit the font open in FontLab 9, and do not stop because the owner might be working in it. Open a VFJ from `~/Desktop` first (those files are for agents), then add glyphs, kerning pairs, elements, contours, masters or whatever the test needs, and save them freely. This supersedes, for live testing, every older line here that forbids mutating owner fonts or documents or requires owned fixtures only. FontLab preferences, Output folders and global update queues stay untouched. Keep the serialized host lock (`fl-native.sh`, one native run at a time; `--mutating` now allows open fonts); do not quit or restart FontLab and do not close fonts from Python, which has crashed the host.
