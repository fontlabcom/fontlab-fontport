#!/bin/sh
# this_file: tests/native_drivers/run-round10.sh
# Offline dry-runs use the same client environment, without starting a host session.
set -eu
FONTPORT_DRIVER_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
FONTPORT_CHECKOUT=$(CDPATH= cd -- "$FONTPORT_DRIVER_DIR/../.." && pwd)
FONTPORT_WORKSPACE=$FONTPORT_CHECKOUT
while [ ! -f "$FONTPORT_WORKSPACE/verification/issue-104/fl-native.sh" ]; do
    [ "$FONTPORT_WORKSPACE" != / ] || { echo 'Cannot locate scripting workspace' >&2; exit 2; }
    FONTPORT_WORKSPACE=$(dirname "$FONTPORT_WORKSPACE")
done
case " $* " in
    *' --dry-run '*|*' --list-tests '*)
        exec uv run --project "$FONTPORT_CHECKOUT" --with "$FONTPORT_WORKSPACE/fontlab-remopy" python "$FONTPORT_DRIVER_DIR/round10.py" --workspace "$FONTPORT_WORKSPACE" "$@" ;;
esac
exec "$FONTPORT_WORKSPACE/verification/issue-104/fl-native.sh" --mutating --lane C4 -- \
    uv run --project "$FONTPORT_CHECKOUT" --with "$FONTPORT_WORKSPACE/fontlab-remopy" python \
    "$FONTPORT_DRIVER_DIR/round10.py" --workspace "$FONTPORT_WORKSPACE" "$@"
