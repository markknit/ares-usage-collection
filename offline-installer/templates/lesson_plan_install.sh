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
step "1. mDNS alias (ares.local) — systemd service"
# ============================================================================
# Works identically whether this box is running its own DHCP/DNS (hotspot
# mode) or is just a client on someone else's router. The publisher prefers
# the normal ARES LAN address and deliberately excludes container, tunnel,
# loopback, link-local, and Tailscale carrier-grade NAT addresses.

if ! command -v avahi-publish >/dev/null 2>&1; then
  fail "avahi-publish not found. Is avahi-utils installed? Skipping mDNS setup — fix manually."
else
  cat > /usr/local/bin/ares-mdns-alias.sh << 'EOF'
#!/bin/bash
# Publishes a fixed mDNS alias (ares.local) pointing at this box's current
# IP. Re-publishes automatically if the IP changes (e.g. DHCP lease renewal
# on boxes that are DNS/DHCP clients rather than the server).
ALIAS="ares.local"
CHECK_INTERVAL=30
current_pid=""
last_ip=""

choose_lan_ip() {
  ip -o -4 address show scope global | python3 -c '
import ipaddress
import sys

candidates = []
for line in sys.stdin:
    fields = line.split()
    if len(fields) < 4:
        continue
    interface = fields[1]
    address = fields[3].split("/", 1)[0]
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError:
        continue
    if interface.startswith(("docker", "br-", "veth", "tailscale", "tun", "tap", "wg")):
        continue
    if parsed.is_loopback or parsed.is_link_local or parsed in ipaddress.ip_network("100.64.0.0/10"):
        continue
    candidates.append((interface, parsed))

for interface, parsed in candidates:
    if str(parsed) == "10.42.0.1":
        print(parsed)
        raise SystemExit(0)
for interface, parsed in candidates:
    if interface.startswith(("wl", "en", "eth")) and parsed.is_private:
        print(parsed)
        raise SystemExit(0)
for interface, parsed in candidates:
    if parsed.is_private:
        print(parsed)
        raise SystemExit(0)
if candidates:
    print(candidates[0][1])
'
}

cleanup() {
  [ -n "$current_pid" ] && kill "$current_pid" 2>/dev/null
  exit 0
}
trap cleanup TERM INT

while true; do
  lan_ip=$(choose_lan_ip)
  if [ -n "$lan_ip" ] && [ "$lan_ip" != "$last_ip" ]; then
    echo "$(date -Is) IP changed: '$last_ip' -> '$lan_ip'. Republishing $ALIAS."
    [ -n "$current_pid" ] && kill "$current_pid" 2>/dev/null
    avahi-publish -a -R "$ALIAS" "$lan_ip" &
    current_pid=$!
    last_ip="$lan_ip"
  elif [ -z "$lan_ip" ] && [ -n "$last_ip" ]; then
    echo "$(date -Is) no eligible LAN IPv4 address; withdrawing $ALIAS."
    [ -n "$current_pid" ] && kill "$current_pid" 2>/dev/null
    current_pid=""
    last_ip=""
  fi
  sleep "$CHECK_INTERVAL"
done
EOF
  chmod +x /usr/local/bin/ares-mdns-alias.sh
  ok "wrote /usr/local/bin/ares-mdns-alias.sh"

  cat > /etc/systemd/system/ares-mdns-alias.service << 'EOF'
[Unit]
Description=Publish fixed mDNS alias (ares.local) for this ARES box
After=network-online.target avahi-daemon.service
Wants=network-online.target
Requires=avahi-daemon.service

[Service]
ExecStart=/usr/local/bin/ares-mdns-alias.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
  ok "wrote /etc/systemd/system/ares-mdns-alias.service"

  systemctl daemon-reload
  systemctl enable --now ares-mdns-alias.service
  sleep 2
  if systemctl is-active --quiet ares-mdns-alias.service; then
    if timeout 8 avahi-resolve -4 -n ares.local >/dev/null 2>&1; then
      ok "ares-mdns-alias.service is running and ares.local resolves"
    else
      fail "ares-mdns-alias.service is running, but ares.local did not resolve"
    fi
  else
    fail "ares-mdns-alias.service did not start — check: systemctl status ares-mdns-alias.service"
  fi
fi

# ============================================================================
step "2. nginx — add ares.local to server_name"
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
elif grep -qE "server_name[^;]*\bares\.local\b" "$NGINX_ACTIVE_CONF"; then
  ok "nginx config already includes ares.local ($NGINX_ACTIVE_CONF) — nothing to do"
else
  cp "$NGINX_ACTIVE_CONF" "$BACKUP_DIR/$(basename "$NGINX_ACTIVE_CONF").bak"
  sed -i -E 's/(server_name[^;]*ares\.edu[^;]*)\s*;/\1 ares.local;/' "$NGINX_ACTIVE_CONF"
  if grep -qE "server_name[^;]*\bares\.local\b" "$NGINX_ACTIVE_CONF"; then
    if nginx -t 2>&1 | grep -q "syntax is ok"; then
      systemctl reload nginx
      ok "added ares.local to $NGINX_ACTIVE_CONF and reloaded nginx"
    else
      cp "$BACKUP_DIR/$(basename "$NGINX_ACTIVE_CONF").bak" "$NGINX_ACTIVE_CONF"
      fail "nginx config test failed after edit — reverted. Check manually: nginx -t"
    fi
  else
    fail "Edit did not apply as expected in $NGINX_ACTIVE_CONF — left unchanged. Patch manually."
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
echo "  ping ares.local"
echo "  (then open the Curriculum Teacher Aids module and click into Grade 10 STEM CBE Lesson Plans)"
echo "  http://ares.local/modules/Lesson_Plans/LESSON3_USER_GUIDE.pdf"
echo ""
echo "Backups of anything replaced are in: $BACKUP_DIR"
exit "$FINAL_RC"
