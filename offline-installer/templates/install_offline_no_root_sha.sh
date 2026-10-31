#!/usr/bin/env bash
# Authorized break-glass recovery only; there is deliberately no automatic yes.
set +x
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -B "$SCRIPT_DIR/recovery_installer.py" "$@"
