#!/bin/sh
# this_file: test.sh
# Run the suite with no setup. fontlab-fontlabapp is not on a package index, so
# use a checkout: $FONTLABAPP_DIR, else the sibling ../fontlab-fontlabapp.
# fontlab-python-pens must be the sibling ../fontlab-python-pens.
# Source tests use the real sibling Fly finder without installing its cohort.
set -eu
here=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
app=${FONTLABAPP_DIR:-}
if [ -z "$app" ]; then
    app="$here/../fontlab-fontlabapp"
fi
if [ -z "$app" ] || [ ! -f "$app/pyproject.toml" ]; then
    echo "test.sh: no fontlab-fontlabapp checkout found." >&2
    echo "Set FONTLABAPP_DIR, or place it at $here/../fontlab-fontlabapp." >&2
    exit 2
fi
pens="$here/../fontlab-python-pens"
if [ ! -f "$pens/pyproject.toml" ]; then
    echo "test.sh: no fontlab-python-pens checkout found." >&2
    echo "Place it at $pens (the suite installs it editable)." >&2
    exit 2
fi
fly="$here/../fontlab-fly"
if [ ! -f "$fly/src/fly/__init__.py" ]; then
    echo "test.sh: no sibling fontlab-fly checkout found at $fly." >&2
    exit 2
fi
export PYTHONPATH="$here/src:$fly/src${PYTHONPATH:+:$PYTHONPATH}"
cd "$here"
exec uv run --no-project --python cpython-3.11-macos-aarch64-none --with pytest --with pytest-cov \
    --with defcon --with 'fontParts>=1.1.1,<1.2' --with fontPens --with fontTools \
    --with ufoLib2 --with-editable "$app" --with-editable "$pens" \
    --with-editable "$here" \
    python -B -m pytest "$@"
