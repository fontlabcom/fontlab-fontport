---
this_file: README.md
---

## Exact UFO feature source

UFO `font.features.get_blocks()` preserves raw prefix and ordered named source
slices, including CR/LF/CRLF, Unicode, missing final newlines and duplicate tags.
`set_blocks()` stores a changed request only when its exact partition survives;
an unchanged request makes no raw write. Ambiguous declarations remain readable
as one prefix and refuse changed structured edits. This stores uncompiled code;
it never follows includes. Native feature history keeps its separate contract.
Saved `features.fea` bytes preserve the source; an upstream UFO reader can still
normalize newlines when reopening it.

## Development status — 2026-11-05

Canonical source inspected for this proposal: `998d59313ea7`. This is a dated source observation, not an installed or native acceptance claim.

Reconcile the Issue 207 candidate with the current DesignSpace/UFO/fontParts boundary; preserve all host data and origin guards.

Qualify native object lifetime, full-font history, Undo/Redo, failure paths and saved/reopened artifacts through matching installed consumers.

## Repository and development

`src/` contains the public package and native adapters; `tests/` has offline contracts; `native-drivers/`, `examples/` and `docs/` hold owned-host drivers and usage. FontLab UI editors belong in App.

Use the explicit arm64 Python 3.11 `fontport_check` recipe in README, with a matching App checkout. `./test.sh` accepts `FONTLABAPP_DIR`, otherwise uses sibling App, and runs pytest with defcon, fontParts, fontPens, fontTools and ufoLib2.

The docs use fly-january 0.3.0 or later for the FontLab menu and footer. Run these commands from the repository root to rebuild `docs/` with the locked Python 3.13 environment.

```sh
uv venv --python 3.13 .docs-venv
. .docs-venv/bin/activate
uv pip install --require-hashes -r src_docs/requirements.txt
sh src_docs/build.sh
```

Keep runtime, ordinary installed artifacts, native workflows and published documentation as separate acceptance results. Track open checks in [TODO.md](TODO.md), the implementation route in [PLAN.md](PLAN.md), and dated evidence in [CHANGELOG.md](CHANGELOG.md).

# Fontport for FontLab

Fontport bridges FontLab 9 to FontParts and UFO data. It provides detached glyph
conversion, live FontParts objects, explicit document access, affine UFO tools
and DesignSpace support. It has no UI. Host use requires Python 3.11 arm64; external Python use requires 3.11 or later.

It uses real fontParts, defcon, fontPens, fontTools and ufoLib2 packages without
replacing their namespaces or registering a world on import. Native imports are lazy; TypeRig is not required.

## Install

To install into FontLab 9, open `install.vfpy` from a checkout in FontLab
(double-click it or drop it onto FontLab), then restart FontLab. The file is a
short stub that hands the work to
[fontlab-instamix](https://github.com/fontlabcom/fontlab-python-instamix); if
instamix is not installed yet, the stub installs it from PyPI first. Instamix
installs the package into FontLab's own `site-packages` and records the install
under the extension id `com.fontlab.fontport`.

FontLab supplies `fontlab`, `fontgate`, `fontpr` and PythonQt. It needs Python
packages built for its own Python 3.11 arm64 runtime. The owner manages editable
installs into FontLab; do not run host install/uninstall commands yourself. Canonical editable sources may differ from this worktree.

Fontport base installation needs no App. The optional `fontlab` extra requires
`fontlab-fontlabapp>=1.2.0` for native edit guards and the legacy feature forwarder.
It does not establish registry availability, native acceptance or a release. `fontlab-fontlabapp` is not on a package
index, so `pip install "fontlab-fontport[fontlab]"` cannot resolve it: install `fontlab-fontlabapp` from a checkout first. For
development, `[tool.uv.sources]` resolves it from the sibling `../fontlab-fontlabapp` checkout, and `uv.lock` records
that path source.
See [dependencies](DEPENDENCIES.md) for package roles and version policy.

## Detached glyphs and pens

Inside FontLab, use a native glyph and an owned destination:

The examples require installed `fontlab-fly>=1.3.0` and their canonical providers.
The source installer copies Scripts but does not install or check Fly. Install
[Fly and its matching providers](https://github.com/fontlabcom/fontlab-fly#install)
separately in the same interpreter before running the Scripts or generated
startup recipes. The Fontport library has no mandatory Fly dependency.

```python
from fly.fp.transfer import to_fontparts, to_ufo_glyph, write_glyph

snapshot = to_fontparts(native_glyph)  # real fontshell.RGlyph
snapshot.width = 600
write_glyph(snapshot, owned_target)   # retains the target name
ufo_glyph = to_ufo_glyph(owned_target)
```

Snapshots contain selected-layer contours, components, anchors, metrics,
Unicodes, note and plist lib data. They are detached; `write_glyph` applies them.
Native hints, guides, images and other layers are outside this conversion slice. Writes stage input and refuse unsupported identifiers, anchor colors, unnamed
anchors, guidelines/images, multiple shapes and transformed targets. An unexpected native assignment error can leave partial changes.

`pens.FontGatePointPen` accepts point-pen calls. Use fontTools'
`SegmentToPointPen` for segment pens; `pens.draw_points` draws to another point
pen. Open, cubic, quadratic and all-offcurve quadratic contours have offline tests. UFO identifiers have no native storage route and are refused.
See [UFO interchange](src_docs/md/guides/UFO-INTERCHANGE.md) for the whole-font sessions and losses.

## Live fonts

Use the chosen document's MCP font id, distinct from its native pointer id:

```python
from fly.fp.host import NativeFontBackend
from fly.fp.live import RFont

font = RFont(NativeFontBackend(font_id))
font["A"].width = 600
font.info.apply({"familyName": "My Family", "ascender": 810.5},
                undo_name="Edit font information")
font.refresh()  # after external edits or Undo; reacquire child handles
font.close()    # detaches this borrowed binding
```

Glyphs are real FontParts RGlyph objects backed by defcon notifications.
The detached `UFOBackend` preserves image filenames, all six transformation
values and color through checked edits, staged `edit_glyph` and backend writes. Image payloads
stay in the existing UFO image set. Native image transfer still refuses images.
Checked `glyph.image.data` reads and writes actual PNG bytes on `UFOBackend`;
failed image transactions restore the target glyph and newly inserted resource.
Shared image assets stay intact. Within `font.edit_glyph`, PNG bytes and actual
image color/transform stay local until the final glyph commits. Clearing an image
discards its pending bytes. Staged glyph/image handles expire on context exit;
reacquire handles after exit or failed refresh. Native image storage and font-level
resource collections remain separate open requirements.
Refresh and `invalidate()` stale loaded child handles; reacquire them after a
rejected edit because rollback can reconstruct the glyph. External same-name replacement needs refresh. `capabilities()` reports explicit backend limits.
Native glyph/layer writes use App's canvas-history guard. In a Glyph window,
change only shown glyphs; create new glyphs from the Font window. No-ops add no
history. Unicode access uses registered font-owned records to avoid fgGlyph's
note-mirror loss; native preservation/history qualification remains pending.

`owns_document=True` closes and discards that document on close; use it only for
owned documents. Existing documents are borrowed by default.

`world.FontWorld` supplies `AllFonts`, `CurrentFont`, `OpenFont`, `NewFont` and
`refresh`. Open/new handles are owned. `world.register()` explicitly connects
`fontParts.world`; `unregister()` restores callbacks. Registration also supports a context manager. Native selection and automatic event subscriptions remain
unavailable. MCP save writes a copy, retains dirty state/source paths, and tracks
the explicit destination in the Fontport handle.

## Font data and current limits

- `info` validates staged metadata before mutation. It supports descriptive name
  strings, metrics, versions, UPM and selected structured UFO fields. Panose,
  OS/2 weight/width and stem snaps use the key master. Changing name records
  refuses without a persistent native route. Concrete native metrics cannot be
  unset with `None`; zero is a value. Strict history/persistence checks are opt-in.
- `font.groups` is a BaseGroups mapping with detached tuple values. `apply`
  replaces all groups; `update` retains unmentioned groups. Dependent kerning
  must remain valid. Native names require printable ASCII; divergent both-sided
  classes refuse. Legacy font-global kerning groups can disappear from VFJ.
- `font.kerning` is BaseKerning with explicit and effective lookup. Zero differs
  from absence; removing an exception restores fallback. Native integer/zero
  Undo/Redo and VFJ checkpoints exist. Fractional values refuse because native
  Redo rounds them; keys also have host name restrictions.
- Features use VFJ-canonical source: `font.features.get_blocks()` and
  `set_blocks({"prefix": text, "features": [(tag, code)]})`. Arbitrary changing
  whole-text replacement is unsupported. `FeatureEdit` stages text for compatible
  models; it does not provide a compiler or bypass the native block boundary.
- Detached lib staging supports plist data. Native packageLib accepts changed
  JSON-compatible leaves, with binary/date writes refused; VFJ can reload nested
  integers as equal-valued floats. Reassign nested values to persist changes.
- Native geometry uses copy-on-write history with an extra no-op checkpoint.
  Hinted outline edits, component replacement and some layer operations remain
  unsupported. Fractional anchors refuse. Exact one-row Undo is not promised.

See [native boundaries](src_docs/md/guides/NATIVE-BOUNDARIES.md), [feature source](src_docs/md/guides/NATIVE-FEATURES.md) and [integration](src_docs/md/guides/INTEGRATION.md). Prior native receipts qualify their recorded build and fixture only.

## Feature source and the moved editors

Fontport has no UI (issue 201). FontLab editors now live in `fontlabapp.fontui`
(App’s optional `fontport` extra); they call Fontport lazily, so install them with
`pip install "fontlab-fontlabapp[fontport]"`. `fontlab_fontport.ui` is a tombstone
for one release: old factory and module access raises `ImportError` naming the
corresponding App home. The restored factories are:

| Factory | Input and purpose |
| --- | --- |
| `font_info_editor(font, parent=None, on_apply=None)` | Stage font information |
| `groups_editor(font, parent=None, on_apply=None)` | Edit explicit groups |
| `kerning_editor(font, parent=None, on_apply=None)` | Inspect/edit kerning |
| `transform_editor(font, name=None, parent=None, on_change=None)` | Preview a detached affine glyph transform |
| `batch_panel(recipe, parent=None, on_finish=None, python=None)` | Run a recipe callback over source UFOs |
| `glyph_sequence(font, parent=None, on_select=None)` | Preview text or slash-separated glyph names |

```python
# old (removed): from fontlab_fontport.ui import font_info_editor
from fly.ap.fontui import font_info_editor

editor = font_info_editor(font)
editor.widget.show()
# Keep editor alive while the panel is open; call editor.close() when finished.
```

App owns these editors, their lifetime, model, preview and canvas mechanics. The UI facade loads no PythonQt or editor module. Moved editor interaction still needs native acceptance. Glyph sequence layout uses Unicode lookup and UFO kerning fallback, not shaping.

Batch work runs in a separate installed Python 3.11+ interpreter. Pass `python=`
or set `FONTLABAPP_BATCH_PYTHON`; Start refuses when neither is set.
The child uses `-I`, ignores PYTHONPATH, and receives only PATH, HOME, TMPDIR,
USER, LOGNAME and locale variables. Install Fontport in that child environment.
Batch destinations must be outside every resolved input UFO tree, including later
inputs, symlink aliases, and case or Unicode spellings that the filesystem
identifies as the same input. Distinct filesystem objects remain distinct.
Existing targets are never overwritten. A destination
folder above the inputs is allowed when the generated UFOs are distinct, absent
siblings outside all input trees. See [the containment defect](https://github.com/Fontlab/fl/issues/8624).
[The App transform example](../fontlab-fontlabapp/examples/font_transform.py) connects preview and batch.
Affine transforms do not preserve stems or provide arbitrary interpolation.
`fontlabapp.fontui.feature_blocks` owns the active-font helpers. The deprecated
`fontlab_fontport.feature_blocks` lazily forwards `read_feature_blocks(package)` and
`write_feature_blocks(package, expected, updated, references=..., undo_name=...)`.
They require the original font to be active. Writes compare the source snapshot
and referenced glyphs, restore the master, and return `{"changed": 0 or 1}`.
Unexpected host failures can leave partial changes. The import is host-free.
Vanilla moved to `fontlab_glyport.ui.session`; `fontlab_fontport.vanilla` no longer exists.
Scripts use App through `fly`; general shared UI belongs in App, Glyphs.app
compatibility in Glyport, and FontParts/UFO code in Fontport.

## Module map

| Modules under `src/fontlab_fontport/` | Role |
| --- | --- |
| `pens`, `transfer` | FontGate pens and detached glyph conversion |
| `backend`, `memory`, `live`, `live_objects`, `lifetime` | Backend protocol, offline models and live handles |
| `host`, `application`, `world`, `capabilities` | Native document bridge, ownership and limits |
| `info`, `groups`, `kerning`, `*_edit`, `native_groups`, `native_kerning` | Data validation, staging and native mappings |
| `fontdata`, `native_features`, `native_feature_split` | Lib and feature source boundaries |
| `ufo_features` | Exact UFO feature source slices and checked structured staging |
| `interchange`, `export`, `paths`, `deploy` | UFO sessions, selected export, absolute paths and startup launcher |
| `recipe`, `recipes`, `operations`, `batch`, `designspace`, `glyphrun` | Affine recipes, batch, axis inspection and sequence layout |
| `designspace_io`, `native_import` | `export_designspace(backend, "Font.designspace")`: axes, sources, instances and one UFO per master (per-master kerning; no rules or per-master groups); `import_designspace(path)` / `import_ufo_native(path)` open them through the native opener |
| `ui/`, `feature_blocks` | UI tombstone (editors moved to `fontlabapp.fontui`) and deprecated lazy feature forwarder |
| `testing`, `testing_exclusions` | Upstream FontParts yardstick and named exclusions |

`tests/` holds offline regressions; `tests/native_drivers/` holds phased host probes (test harness, not shipped);
`examples/fontparts/` has 19 owned-font examples. `tools/fontparts-coverage.py` maintains [the coverage report](src_docs/md/guides/FONTPARTS-COVERAGE.md).
Current next steps are in [PLAN](PLAN.md) and [TODO](TODO.md).

## Testing

Run from this checkout with uv, network access and reviewed App source beside it.
uv needs arm64 Python 3.11 or permission to download it. Set `FONTLAB_SCRATCH` to a writable external-drive folder first; both packages install externally for isolated batch children.

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
Checks run the offline suite, docs and lint; optional compilation needs ufo2ft. The project launcher uses an outdated lock.

Offline tests are not native proof. Native work needs installed artifacts,
owned fixtures, import-origin checks and Apply/Undo/Redo/save/reopen comparisons
in a dedicated FontLab session. Restart after each mutating suite; never use
borrowed user documents. Pass absolute paths and split work around the fixed
five-second host deadline. Do not construct a QApplication or second event loop.
The startup launcher is a file for host startup, not input to `run_python`.

## Licence

Apache License 2.0; see [LICENSE](LICENSE). Dependencies retain their own licences. No private font corpus or proprietary native source is included.

[Scripts demos](Scripts/README.md) use detached sample data, with host-free `build_report()` results and optional FontLab report windows through Fly/App. No open font is required.
