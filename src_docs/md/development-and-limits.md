---
this_file: src_docs/md/development-and-limits.md
---

# Development and limits

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


## Complete classification and native boundary

The [FontParts ledger](guides/FONTPARTS-COVERAGE.md) retains all 1,797 upstream test IDs, both native classifications and their exact observed counts. The round guides retain dated build, fixture, history, Undo/Redo and saved/reopened qualifiers. The [native manifest](https://github.com/fontlabcom/fontlab-fontport/blob/bbe74e286b8281ae22b383cf42755d9d084c8aae/verification/issue-105/NATIVE-MANIFEST.json) remains exact source-distribution provenance. This documentation build does not regenerate acceptance, execute native drivers or install into the owner environment. Private Pages configuration and publication remain owner-held.
