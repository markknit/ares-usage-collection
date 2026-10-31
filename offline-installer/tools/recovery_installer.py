#!/usr/bin/env python3
"""Explicit, interactive root-manifest recovery; reuse the verified workflow."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

from package_integrity import operator_identity, receipt

CONFIRMATION = "INSTALL UNVERIFIED PACKAGE"
WARNING = "WARNING: ROOT PACKAGE SHA256SUMS INTENTIONALLY SKIPPED - NOT FULLY VERIFIED"
DRIVER = r'''
set -Eeuo pipefail
readonly RECOVERY_PACKAGE_DIR="$(cd -- "$1" && pwd)"
shift
RECOVERY_PREFLIGHT_RAN=0
bash() {
  if [[ $# -eq 2 && "$1" == "$RECOVERY_PACKAGE_DIR/preflight.sh" ]]; then
    (source "$RECOVERY_PACKAGE_DIR/preflight.sh"; preflight_main recovery "$2")
    RECOVERY_PREFLIGHT_RAN=1
  else
    command bash "$@"
  fi
}
source "$RECOVERY_PACKAGE_DIR/install_offline.sh" "$@"
[[ "$RECOVERY_PREFLIGHT_RAN" == 1 ]] || { echo "ERROR: recovery preflight did not execute" >&2; exit 1; }
'''


def confirm_recovery(stream=None, output=None):
    stream = sys.stdin if stream is None else stream
    output = sys.stderr if output is None else output
    if not os.isatty(stream.fileno()):
        raise ValueError("Recovery requires an interactive terminal on stdin; piped confirmation is rejected")
    print(WARNING, file=output)
    print("Only verification of this bundle's ROOT SHA256SUMS will be skipped.", file=output)
    print("Required files, preflight, APK approval/profile, Lesson3 release/images/corpus,", file=output)
    print("TsavoTrust, Tailscale and TigerVNC component checks all remain active.", file=output)
    print("Use only for an authorized, deliberately modified package from a trusted source.", file=output)
    print("Do not proceed for unexplained corruption, missing files or failed component hashes.", file=output)
    print("Type exactly: " + CONFIRMATION, file=output, flush=True)
    value = stream.readline()
    if value.rstrip("\r\n") != CONFIRMATION:
        raise ValueError("Recovery confirmation rejected; no installation was started")


def run_recovery(package, school, state_dir=Path("/var/lib/ares/offline-installer/receipts"), log_dir=Path("/var/log")):
    package = Path(package).resolve()
    # Keep the normal entry point byte-for-byte unchanged. Its preflight command
    # is the sole dispatch point; every other bash call runs normally. A changed
    # contract fails closed instead of silently broadening the exception.
    anchor = 'bash "$SCRIPT_DIR/preflight.sh" "$SCHOOL_CODE"'
    if (package / "install_offline.sh").read_text(encoding="utf-8").count(anchor) != 1:
        raise ValueError("Verified installer preflight contract changed; review the recovery adapter")
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log = log_dir / ("ares-offline-recovery-" + uuid.uuid4().hex + ".log")
    record = receipt(state_dir, "recovery", "authorized")
    def audit(message):
        descriptor = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
            handle.write(datetime.now(timezone.utc).isoformat() + " operator=" + operator_identity() + " " + message + "\n")
    audit(WARNING)
    print(WARNING, flush=True)
    print("Recovery audit:", log, "Receipt:", record, flush=True)
    code = 1
    try:
        result = subprocess.run(["bash", "-c", DRIVER, "ares-root-recovery", package.as_posix(), school])
        code = result.returncode if result.returncode >= 0 else 128 - result.returncode
    except KeyboardInterrupt:
        code = 130
    finally:
        phase = "installation_completed" if code == 0 else "installation_failed"
        receipt(state_dir, "recovery", phase, code, path=record)
        audit(WARNING + " phase=" + phase + " exit_code=" + str(code))
        print(WARNING, flush=True)
        print("Recovery result:", phase, "- component checks retained; root package integrity NOT verified.", flush=True)
        print("Recovery receipt:", record, flush=True)
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("school_code")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Z0-9_-]+", args.school_code):
        parser.error("invalid school code")
    try:
        confirm_recovery()
        if not hasattr(os, "geteuid") or os.geteuid() != 0:
            raise ValueError("Run recovery as root on the Ubuntu target")
        return run_recovery(Path(__file__).resolve().parent, args.school_code)
    except (ValueError, OSError) as error:
        print("ERROR:", error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
