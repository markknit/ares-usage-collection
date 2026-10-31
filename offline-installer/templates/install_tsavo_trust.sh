#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
(cd "$SCRIPT_DIR" && sha256sum -c SHA256SUMS)
exec python3 "$SCRIPT_DIR/tsavo_install.py" "$@"
