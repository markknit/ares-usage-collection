#!/bin/bash
# ============================================================================
# ARES Curriculum Teacher Aids — PDF module deployment + ares.local mDNS setup
#
# Run this ONCE on each ARES server (~100 total). Safe to re-run if something
# fails partway — every step checks before it acts.
#
# What this does:
#   1. Installs/updates the "ares.local" mDNS alias (works whether this box
#      is a DHCP/DNS server itself, or just a client on someone else's network)
#   2. Adds "ares.local" to nginx's server_name so the tracker/Kolibri/Kiwix
#      proxy routes still match requests made to that hostname
#   3. Deploys the Grade 10 CBE lesson plan PDFs + teacher index page
#   4. Deploys generate_teacher_index.js (lets this box re-index locally later
#      if PDFs are updated without re-running this whole script)
#   5. Deploys the Lesson3 User Guide and replaces the module landing/details pages
#
# MUST be run as root (or with sudo) — it edits systemd and nginx.
# ============================================================================

set -u  # error on unset variables; deliberately NOT using -e — we want to
        # keep going and report every step's pass/fail rather than die silently
        # partway through a 100-server rollout.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../ares_config.sh" "$SCRIPT_DIR/../package.conf"
PAYLOAD_DIR="$SCRIPT_DIR/payload"
MODULE_DIR="/mnt/sda3/var/www/modules/Lesson_Plans"
PDF_DIR="$MODULE_DIR/PDF"
BACKUP_DIR="/root/ares_deploy_backups/$(date +%Y%m%d_%H%M%S)"
STEP_FAILURES=0

# ---- helpers ---------------------------------------------------------------
step() { echo ""; echo "=== $1 ==="; }
ok()   { echo "  OK: $1"; }
fail() { echo "  FAILED: $1"; STEP_FAILURES=$((STEP_FAILURES + 1)); }
warn() { echo "  WARNING: $1"; }

if [ "$(id -u)" -ne 0 ]; then
  echo "This script must be run as root (try: sudo bash install.sh)"
  exit 1
fi

if [ ! -d "$PAYLOAD_DIR" ]; then
  echo "Cannot find payload/ directory next to this script. Did you unzip everything together?"
  exit 1
fi

mkdir -p "$BACKUP_DIR"
echo "Backups of anything replaced will be saved to: $BACKUP_DIR"

# ============================================================================
step "1. mDNS alias ($ARES_ALIAS) — systemd service"
# ============================================================================
# Avahi retains hostname.local; the separate publisher adds the generic alias.
# An unplugged LAN is a normal deployment state, not a failed installation.
if bash "$SCRIPT_DIR/configure_mdns.sh"; then
  ok "installed $ARES_ALIAS alongside $(hostname -s).local"
else
  fail "mDNS setup failed; check avahi-daemon and ares-mdns-alias services"
fi

# ============================================================================
step "2. nginx — configure $ARES_ALIAS in server_name"
# ============================================================================
# Different boxes may have differently-named site config files (we found
# NINE variously-named backups on one test box alone) — so this resolves
# whatever is ACTUALLY symlinked live in sites-enabled, rather than
# assuming a filename like "default".

NGINX_ACTIVE_CONF=""
for candidate in /etc/nginx/sites-enabled/*; do
  [ -L "$candidate" ] || continue
  target=$(readlink -f "$candidate")
  if [ -f "$target" ] && grep -q "server_name.*ares" "$target" 2>/dev/null; then
    NGINX_ACTIVE_CONF="$target"
    break
  fi
done

if [ -z "$NGINX_ACTIVE_CONF" ]; then
  fail "Could not find an active nginx config with an 'ares' server_name. Skipping — patch manually."
else
  cp "$NGINX_ACTIVE_CONF" "$BACKUP_DIR/$(basename "$NGINX_ACTIVE_CONF").bak"
  if python3 "$SCRIPT_DIR/configure_nginx.py" "$NGINX_ACTIVE_CONF" "$ARES_ALIAS" "$(hostname -s).local" && nginx -t; then
    systemctl reload nginx || fail "Nginx reload failed"
    ok "configured $ARES_ALIAS in $NGINX_ACTIVE_CONF"
  else
    cp "$BACKUP_DIR/$(basename "$NGINX_ACTIVE_CONF").bak" "$NGINX_ACTIVE_CONF"
    fail "Nginx profile configuration failed; restored backup"
  fi
fi

# ============================================================================
step "3. Deploy PDF content"
# ============================================================================
if [ ! -d "$PAYLOAD_DIR/PDF" ]; then
  fail "payload/PDF/ not found — nothing to deploy"
else
  mkdir -p "$MODULE_DIR"
  if [ -d "$PDF_DIR" ]; then
    tar -czf "$BACKUP_DIR/PDF_old.tar.gz" -C "$MODULE_DIR" PDF 2>/dev/null \
      && ok "backed up existing PDF/ to $BACKUP_DIR/PDF_old.tar.gz" \
      || warn "could not back up existing PDF/ (may not have existed yet)"
  fi
  if rsync -a --delete "$PAYLOAD_DIR/PDF/" "$PDF_DIR/"; then
    ok "synced PDF content to $PDF_DIR"
  else
    fail "rsync of PDF content to $PDF_DIR failed"
  fi
fi

# ============================================================================
step "4. Deploy generate_teacher_index.js"
# ============================================================================
if [ ! -f "$PAYLOAD_DIR/generate_teacher_index.js" ]; then
  fail "payload/generate_teacher_index.js not found"
else
  mkdir -p "$PDF_DIR"
  if cp "$PAYLOAD_DIR/generate_teacher_index.js" "$PDF_DIR/generate_teacher_index.js"; then
    ok "deployed generate_teacher_index.js to $PDF_DIR (for future local re-indexing)"
  else
    fail "could not deploy generate_teacher_index.js to $PDF_DIR"
  fi
fi

# ============================================================================
step "5. Deploy module landing page (index.htmlf)"
# ============================================================================
TEACHER_AIDS_DIR="/mnt/sda3/var/www/modules/Curriculum_Teacher_Aids"
TEACHER_LINK="/mnt/sda3/var/www/www_teacher/modules/Lesson_Plans"

# The SeaVuria logo has existed under two spellings in earlier packages.
# Accept either source name, but deploy one canonical web filename.
SEAVURIA_LOGO_SRC=""
for candidate in \
  "$PAYLOAD_DIR/SeaVuria-Logo-2.jpg" \
  "$PAYLOAD_DIR/SeaVuria-Logo2.jpg" \
  "$PAYLOAD_DIR/Seavuria-Logo-2.jpg" \
  "$PAYLOAD_DIR/Seavuria-Logo2.jpg"; do
  if [ -f "$candidate" ]; then
    SEAVURIA_LOGO_SRC="$candidate"
    break
  fi
done

missing_payload=0
for required in index.htmlf index.html index_bu.htmlf ARES-Logo.png LESSON3_USER_GUIDE.pdf; do
  if [ ! -f "$PAYLOAD_DIR/$required" ]; then
    fail "payload/$required not found"
    missing_payload=1
  fi
done
if [ -z "$SEAVURIA_LOGO_SRC" ]; then
  warn "SeaVuria logo not found in payload/; continuing without the decorative partner logo"
fi

if [ "$missing_payload" -eq 0 ]; then
  mkdir -p "$MODULE_DIR" "$TEACHER_AIDS_DIR" "$(dirname "$TEACHER_LINK")"

  if [ -f "$MODULE_DIR/index.htmlf" ]; then
    cp "$MODULE_DIR/index.htmlf" "$BACKUP_DIR/index.htmlf.bak" \
      && ok "backed up existing index.htmlf to $BACKUP_DIR/index.htmlf.bak" \
      || warn "could not back up existing index.htmlf"
  fi

  deploy_ok=1
  cp "$PAYLOAD_DIR/index.htmlf" "$MODULE_DIR/index.htmlf" || deploy_ok=0
  cp "$PAYLOAD_DIR/index.html" "$MODULE_DIR/index.html" || deploy_ok=0
  cp "$PAYLOAD_DIR/index_bu.htmlf" "$TEACHER_AIDS_DIR/index.htmlf" || deploy_ok=0
  cp "$PAYLOAD_DIR/ARES-Logo.png" "$MODULE_DIR/ARES-Logo.png" || deploy_ok=0
  if [ -f "$MODULE_DIR/LESSON3_USER_GUIDE.pdf" ]; then
    cp "$MODULE_DIR/LESSON3_USER_GUIDE.pdf" "$BACKUP_DIR/LESSON3_USER_GUIDE.pdf.bak" \
      || warn "could not back up existing Lesson3 User Guide"
  fi
  cp "$PAYLOAD_DIR/LESSON3_USER_GUIDE.pdf" "$MODULE_DIR/LESSON3_USER_GUIDE.pdf" || deploy_ok=0
  if [ "$deploy_ok" -eq 1 ] && [ "$(head -c 5 "$MODULE_DIR/LESSON3_USER_GUIDE.pdf" 2>/dev/null)" != "%PDF-" ]; then
    deploy_ok=0
    warn "deployed Lesson3 User Guide does not appear to be a valid PDF"
  fi
  if [ -n "$SEAVURIA_LOGO_SRC" ]; then
    cp "$SEAVURIA_LOGO_SRC" "$MODULE_DIR/SeaVuria-Logo-2.jpg" || deploy_ok=0
  else
    rm -f "$MODULE_DIR/SeaVuria-Logo-2.jpg"
  fi

  if [ "$deploy_ok" -eq 1 ]; then
    chown -R ares:www-data "$MODULE_DIR" || warn "could not set ownership on $MODULE_DIR"

    if [ -L "$TEACHER_LINK" ]; then
      ln -sfn "$MODULE_DIR" "$TEACHER_LINK"
    elif [ -e "$TEACHER_LINK" ]; then
      warn "$TEACHER_LINK already exists and is not a symlink; leaving it unchanged"
    else
      ln -s "$MODULE_DIR" "$TEACHER_LINK" || deploy_ok=0
    fi
  fi

  if [ "$deploy_ok" -eq 1 ]; then
    ok "deployed Lesson Plans module and Lesson3 User Guide to $MODULE_DIR"
  else
    fail "one or more Lesson Plans deployment commands failed"
  fi
fi

# ============================================================================
step "SUMMARY"
# ============================================================================
if [ "$STEP_FAILURES" -eq 0 ]; then
  echo "All steps completed successfully."
  FINAL_RC=0
else
  echo "$STEP_FAILURES step(s) failed — see FAILED lines above. Fix those manually before considering this box done."
  FINAL_RC=1
fi
echo ""
echo "Verify manually from ANOTHER device on this school's network:"
echo "  ping $ARES_ALIAS"
echo "  (then open the Curriculum Teacher Aids module and click into Grade 10 STEM CBE Lesson Plans)"
echo "  $ARES_URL/modules/Lesson_Plans/LESSON3_USER_GUIDE.pdf"
echo ""
echo "Backups of anything replaced are in: $BACKUP_DIR"
exit "$FINAL_RC"
