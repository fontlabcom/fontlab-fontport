---
this_file: DEPENDENCIES.md
---

## Conditional installer requirements

Only conditional installer requirements use `packaging==26.3` in an external uv-managed Python environment. FontLab itself imports only the standard library; no permanent project dependency was added. An unavailable helper fails before sibling execution.



Round 10 uses these same real upstream packages: fontParts.test (1.1.1) supplies
the 1,797-ID yardstick and fontshell parity; defcon supplies live models and
notifications; ufoLib2 supplies the host-free backend and whole-UFO staging;
fontPens supplies Digest/Flatten/Margin/TransformPoint pens; fontTools supplies
GLIF/UFO serialization, Bounds/Recording/Transform pens, feaLib and designspaceLib.
No new dependency or namespace replacement was added. Native event subscription
is unavailable and is exposed as a capability flag rather than emulated.

# Dependencies

| Package | Purpose |
| --- | --- |
| fontParts >=1.1.1,<1.2 | Real FontParts objects; dispatcher compatibility tested against 1.1.1 |
| defcon 0.12+ | Live glyph objects, change notifications and rollback snapshots |
| fontlab-python-pens | Zero-dependency fontTools-compatible pen protocol for FontLab layers and elements; the FontGate point pen and reader (Issue 235). Unpublished: resolved from the sibling checkout, unpinned (untagged dev version) |
| fontTools | Point/segment pen protocols, geometry and UFO tools |
| fontPens | Existing composable pen algorithms |
| ufoLib2 | UFO3 interchange and persistence |
| hatchling / hatch-vcs | Packaging and Git-derived versions |
| pytest / pytest-cov | Development verification |
| ufo2ft (`fontbuild` extra) | Optional external TTF compilation of the selected UFO geometry export |

FontParts also installs booleanOperations and fontMath; defcon is a direct
dependency because the live environment imports it explicitly. No
vendor UI source, proprietary native source or research corpus is distributed.
Tested dependency versions: see "Lock and test commands" below; native use requires Python
3.11 packages for the architecture used by FontLab.

No new mandatory dependency was added for the X3 integration. Designspace,
transform pens and structured info validation use the already-required
fontTools; detached batch artifacts use the already-required ufoLib2. The Vanilla
session moved to Glyport (issue 122); Fontport has no UI-toolkit dependency.

Issue 105 row 15 permits `typerig-lib`; Fontport currently does **not** depend
on or import it. Its pens/geometry use fontTools/fontPens, its public objects
use FontParts/defcon, its persistence uses ufoLib2 and its native adapters call
FontGate/FontLab directly. Adding TypeRig would add a second proxy/object layer
without supplying a missing current contract. In particular, TypeRig's
`Lib/typerig/proxy/fl/objects/font.py` feature helpers wrap the same
`fg.features` prefix/per-tag API. Its `setFeaPrefix` currently calls
`get_prefix(feaString)` instead of `set_prefix`; Fontport uses the direct native
setters and the canonical fontpr serializer. TypeRig is not vendored
or implicitly imported; this decision can be revisited for a concrete missing
operation after checking its native contract and tests.

Round-11 native client execution uses this checkout's dependency environment
plus the local fontlab-remopy project via uv --with. Dry-runs use that identical
resolution and never import or contact Remopy/FontLab. Native host dependency
versions must still match the startup receipts; restart before each suite.


## Optional FontLab integration: `fontlab` extra

Base DesignSpace/UFO/fontParts use has no App dependency. The `fontlab` extra
requires `fontlab-fontlabapp>=1.2.0` for `host.py`'s four lazy
`fontlabapp.core.edit_guards` imports and the deprecated `feature_blocks` forwarder.
The UI modules and active-font feature helper implementation live in
`fontlabapp.fontui`. App's optional `fontport = ["fontlab-fontport"]` extra
supplies their FontParts stack; neither package has a hard dependency cycle.
The AST tests enforce the allowed paths and lazy optional imports.
Versions still come from real hatch-vcs ancestry. The 1.2.0 release floor
requires the canonical App layout; it does not establish registry availability
or native acceptance.
App imports Fontport only lazily, in its `fontlabapp.fontui` FontParts editors
behind the `fontlab-fontlabapp[fontport]` extra (issue 201); Fontport adds no
duplicated fallback or Glyport dependency. App is not published, so
`[tool.uv.sources]` resolves it from the sibling `../fontlab-fontlabapp`
checkout. Use the reviewed candidate wheel or source; never set SCM
pretend-version variables to satisfy the dependency.

## Lock and test commands

`uv.lock` is not refreshed: it has no `fontlab-fontlabapp` entry. A lock that
resolves App would point at a local path or registry, so a relock needs the
owner's agreement. Until then explicit `--no-project` source checks and ordinary
artifact installation are the development routes; `sh test.sh`, frozen sync and
`uv run --extra test` do not establish the current closure. From this checkout,
with reviewed App source beside it, clear every inherited version fabrication:

```bash
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

For an ordinary install into a disposable external Python 3.11 arm64 environment,
provide the reviewed Fontport wheel (add the App wheel for native integration):

```bash
uv pip install --no-config --python "$CHECK_ENV/bin/python" "$APP_WHEEL" "$FONTPORT_WHEEL"
```

Set those paths to the external environment and reviewed artifacts. Normal
resolution must succeed without dependency bypasses or overrides. This does not
change the owner-managed FontLab environment. Fontport must be installed for
isolated batch children; `PYTHONPATH` alone is insufficient. Lint with
`uvx --no-config ruff check src tests`. Use the writable external TMP/cache described in README.

The explicit `--no-config` routes ignore local/user uv configuration, including
legacy project overrides; normal dependency metadata still governs resolution.

## Documentation build

The separate Python 3.13 docs environment uses `src_docs/requirements.txt`. It pins fly-january 0.1.1, ProperDocs 1.6.7, MkDocs 1.6.1, MaterialX 10.1.8 and PyMdown 11.0.1 with hashes. The Fly plugin supplies FontLab chrome and connects the site's English search to MaterialX. Host and ordinary artifact checks explicitly select arm64 CPython 3.11 and assert the actual architecture.
