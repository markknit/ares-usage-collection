#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

usage() {
  cat <<'USAGE'
Usage:
  sudo bash local-server/update_school_server.sh --school-code ARES-S00XX [installer options]

Run this command from a vetted ARES usage-collection release folder. It calls
install_usage_collection.sh in update mode, which:

  * validates the release files and approved production schedule;
  * verifies the existing report builder and source CSV before changing files;
  * backs up every replaced component;
  * installs all current school-server components;
  * replaces the server schedule with the release's approved schedule; and
  * runs an AUTO export smoke test and reports the measured CSV size.

All options except --replace-schedule are passed to install_usage_collection.sh.
The approved release schedule is always replaced intentionally in update mode.
USAGE
}

for arg in "$@"; do
  case "$arg" in
    -h|--help)
      usage
      exit 0
      ;;
    --replace-schedule)
      echo "ERROR: --replace-schedule is automatic in update mode; do not pass it twice" >&2
      exit 1
      ;;
  esac
done

exec bash "$SCRIPT_DIR/install_usage_collection.sh" --replace-schedule "$@"
