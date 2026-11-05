from pathlib import Path
import os
import sys
import tempfile
import subprocess
import hashlib
import io
import shutil
import tarfile
import unittest
from test_profiles import BASH, BUILDER, load

config = load("remote_support_config")
urls = load("configure_lesson3_url")


def shell(source, code):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        shim = root / "python3"
        shim.write_text('#!/bin/bash\nexec "' + Path(sys.executable).as_posix() + '" "$@"\n', newline="\n")
        shim.chmod(0o755)
        prefix = 'export PATH="$(cygpath -u "$4"):$PATH"; ' if os.name == "nt" else 'export PATH="$4:$PATH"; '
        result = subprocess.run([BASH, "-c", prefix + 'source "$2"; source "$1"; CONFIG_TOOL="$3"; STATE_DIR="$4"; ' + code,
                                 "test", (BUILDER / "templates" / source).as_posix(),
                                 (BUILDER / "templates/remote_support_common.sh").as_posix(),
                                 (BUILDER / "tools/remote_support_config.py").as_posix(), root.as_posix()],
                                capture_output=True, text=True)
        result.artifacts = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        return result


SYSTEMD_FIXTURE = r'''
CALLS="$STATE_DIR/calls"
declare -A ACTIVE=([ssh.service]=no [ssh.socket]=yes [tailscaled.service]=yes [tigervncserver@:1.service]=no)
declare -A ENABLED=([ssh.service]=disabled [ssh.socket]=enabled)
declare -A PRESENT=([ssh.service]=yes [ssh.socket]=yes [tigervncserver@.service]=yes)
systemctl() {
  printf '%s\n' "$*" >> "$CALLS"
  local action=$1 unit="${@: -1}" item
  case "$action" in
    cat) [[ "${PRESENT[$unit]:-no}" == yes ]] ;;
    is-active) [[ "${ACTIVE[$unit]:-no}" == yes ]] ;;
    is-enabled) printf '%s\n' "${ENABLED[$unit]:-disabled}"; [[ "${ENABLED[$unit]:-disabled}" == enabled* ]] ;;
    enable|disable|start|stop|restart|mask)
      for item in "${@:2}"; do
        [[ "$item" != --* ]] || continue
        case "$action" in
          enable) ENABLED[$item]=enabled; [[ "$*" != *--runtime* ]] || ENABLED[$item]=enabled-runtime; [[ "$*" != *--now* ]] || ACTIVE[$item]=yes ;;
          disable) [[ "${ENABLED[$item]:-disabled}" == static ]] || ENABLED[$item]=disabled; [[ "$*" != *--now* ]] || ACTIVE[$item]=no ;;
          start|restart) ACTIVE[$item]=yes ;;
          stop) ACTIVE[$item]=no ;;
          mask) ENABLED[$item]=masked ;;
        esac
      done
      return 0 ;;
    status) echo VNC_STATUS; return 3 ;;
    *) return 0 ;;
  esac
}
'''


class RemoteSupportTests(unittest.TestCase):
    def test_preparation_preserves_live_support_and_never_disables_console_sharing(self):
        for active in (False, True):
            with self.subTest(active=active), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                remote, bin_dir = root / 'remote', root / 'bin'
                for directory in (remote / 'tigervnc', remote / 'tailscale', bin_dir,
                                  root / 'etc/systemd/system', root / 'etc/default',
                                  root / 'share/xsessions', root / 'local/bin', root / 'local/sbin'):
                    directory.mkdir(parents=True, exist_ok=True)
                (root / 'etc/os-release').write_text('ID=ubuntu\nVERSION_ID=24.04\n')
                (root / 'share/xsessions/cinnamon2d.desktop').touch()
                for name, source in {
                    'ares_enable_remote_access.sh': 'templates/ares_enable_remote_access.sh',
                    'ares_disable_remote_access.sh': 'templates/ares_disable_remote_access.sh',
                    'remote_support_common.sh': 'templates/remote_support_common.sh',
                    'remote_support_config.py': 'tools/remote_support_config.py',
                }.items():
                    shutil.copyfile(BUILDER / source, remote / name)
                    (remote / name).chmod(0o755)
                for i in range(4):
                    (remote / 'tigervnc' / f'fixture{i}.deb').write_text('fixture')
                with tarfile.open(remote / 'tailscale/tailscale_fixture_amd64.tgz', 'w:gz') as archive:
                    for name in ('tailscale', 'tailscaled'):
                        data = b'#!/usr/bin/env bash\nexit 0\n'
                        info = tarfile.TarInfo('tailscale/' + name)
                        info.mode = 0o755
                        info.size = len(data)
                        archive.addfile(info, io.BytesIO(data))
                for component in ('tigervnc', 'tailscale'):
                    folder = remote / component
                    (folder / 'SHA256SUMS').write_text(''.join(
                        hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n'
                        for p in sorted(folder.iterdir())), newline='\n')
                commands = {
                    'uname': 'echo x86_64',
                    'cinnamon-session-cinnamon2d': 'exit 0',
                    'tigervncserver': 'exit 0', 'tigervncpasswd': 'exit 0',
                    'pgrep': 'exit 0',  # Existing x11vnc is always retained.
                    'ss': '[[ "$ACTIVE" != yes ]] || echo "LISTEN 0 5 127.0.0.1:5901"; exit 0',
                    'dpkg-query': 'exit 1',
                    'dpkg': 'echo "dpkg $*" >> "$CALLS"',
                    'systemctl': 'echo "systemctl $*" >> "$CALLS"\nif [[ "$1" == is-active ]]; then [[ "$ACTIVE" == yes ]]; else exit 0; fi',
                }
                for name, body in commands.items():
                    path = bin_dir / name
                    path.write_text('#!/bin/bash\n' + body + '\n', newline='\n')
                    path.chmod(0o755)
                marker = root / 'local/bin/tailscale'
                marker.write_text('retain enrolled binary')
                text = (BUILDER / 'templates/prepare_remote_access.sh').read_text()
                text = text.replace('[[ ${EUID:-$(id -u)} -eq 0 ]] || die "run as root"', '')
                text = text.replace('/usr/local/', (root / 'local').as_posix() + '/')
                text = text.replace('/usr/share/', (root / 'share').as_posix() + '/')
                text = text.replace('/etc/', (root / 'etc').as_posix() + '/')
                text = text.replace('/tmp/ares-tailscale', root.as_posix() + '/tailscale-work')
                if os.name == 'nt':
                    # Native Ubuntu checks real executable bits; Git Bash on
                    # NTFS cannot represent the TAR's Unix execute permissions.
                    text = text.replace(' -perm -u+x', '')
                script = remote / 'prepare.sh'
                script.write_text(text, newline='\n')
                prefix = 'export PATH="$(cygpath -u "$1"):$PATH"; ' if os.name == 'nt' else 'export PATH="$1:$PATH"; '
                result = subprocess.run([BASH, '-c', prefix + 'exec bash "$2"', 'fixture',
                                         bin_dir.as_posix(), script.as_posix()], capture_output=True, text=True,
                                        env=dict(os.environ, ACTIVE='yes' if active else 'no',
                                                 CALLS=(root / 'calls').as_posix()))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                calls = (root / 'calls').read_text()
                self.assertNotIn('disable', calls)
                self.assertNotIn('stop', calls)
                self.assertNotIn('restart', calls)
                self.assertNotIn('systemctl enable', calls)
                if active:
                    self.assertEqual(marker.read_text(), 'retain enrolled binary')
                    self.assertNotIn('dpkg -i', calls)
                else:
                    self.assertIn('dpkg -i', calls)
                self.assertIn('x11vnc console sharing is retained', result.stdout)

    def test_empty_remote_name_retains_current_hostname_and_invalid_name_reprompts(self):
        for values, expected in (("\\n\\n", 'tsavo3'),
                                 ("!!!\\nExample School\\ny\\n", 'example-school')):
            result = shell('ares_enable_remote_access.sh', '''
OLD_HOSTNAME=tsavo3
exec 3>"$STATE_DIR/terminal"
''' + "exec 4<<<$'" + values + "'\nchoose_remote_hostname\n[[ \"$SELECTED_HOSTNAME\" == \"" + expected + "\" ]]\n")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('Traceback', result.stdout + result.stderr)

    def test_cancelled_remote_name_is_deferred_without_a_traceback(self):
        result = shell('ares_enable_remote_access.sh', '''
OLD_HOSTNAME=tsavo3
exec 3>"$STATE_DIR/terminal"; exec 4</dev/null
choose_remote_hostname
''')
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertNotIn('Traceback', result.stdout + result.stderr)

    def test_hosts_preserves_aliases_comments_and_actual_separators(self):
        value = "127.0.0.1 localhost\n127.0.1.1 old retained ares.local # comment\n"
        changed = config.hosts(value, "old", "new")
        self.assertEqual(changed, "127.0.0.1 localhost\n127.0.1.1\tnew retained ares.local # comment\n")
        self.assertNotIn("\\t", changed)
        self.assertEqual(config.hosts(changed, "new", "new"), changed)

    def test_display_conflicts_fail_and_other_displays_survive(self):
        with self.assertRaises(ValueError):
            config.display_map(":1 = another-user\n")
        value = config.display_map("# retained\n:2=other\n:1=ares\n:1=ares\n")
        self.assertEqual(value, "# retained\n:2=other\n:1=ares\n")
        self.assertEqual(config.display_map(value), value)

    def test_hostname_normalization_and_limits(self):
        self.assertEqual(config.hostname(" St Jude Nturukhuma Girls "), "st-jude-nturukhuma-girls")
        self.assertLessEqual(len(config.hostname("a" * 100)), 63)
        with self.assertRaises(ValueError):
            config.hostname("!!!")

    def test_lesson3_urls_preserve_secrets_and_offline_posture(self):
        for alias in ("ares.local", "ares-test.local"):
            original = "SECRET=unchanged\nADMIN_URL=http://localhost:3001\nSERVER_URL=\n"
            expected = "http://" + alias + ":3001"
            changed = urls.configure(original, expected, "")
            self.assertIn("SECRET=unchanged\n", changed)
            self.assertIn("ADMIN_URL=" + expected + "\nSERVER_URL=\n", changed)
            self.assertEqual(urls.configure(changed, expected, ""), changed)
            with self.assertRaises(ValueError):
                urls.configure(original, expected, expected)

    def test_vnc_rejects_all_nonloopback_listeners(self):
        for addresses, passes in (("127.0.0.1:5901 [::1]:5901", True),
                                  ("127.0.0.1:5901 192.168.1.2:5901", False),
                                  ("0.0.0.0:5901", False), ("[::]:5901", False), ("", False)):
            rows = "\n".join("LISTEN 0 5 " + value + " *:*" for value in addresses.split())
            result = shell("ares_enable_remote_access.sh", "ss() { printf '%s\\n' '" + rows + "'; }; verify_vnc_listeners")
            self.assertEqual(result.returncode == 0, passes, result.stderr)

    def test_vnc_failure_preserves_command_line_and_diagnoses_before_stop(self):
        result = shell("ares_enable_remote_access.sh", SYSTEMD_FIXTURE + '''
TARGET_HOME="$STATE_DIR/home"; mkdir -p "$TARGET_HOME/.vnc"
echo VNC_CURRENT_LOG > "$TARGET_HOME/.vnc/fixture:1.log"
journalctl() { echo VNC_JOURNAL; }
runuser() { shift 3; "$@"; }
print_ssh_instructions() { echo SSH_RETAINED; }
STARTED=1; CLI_READY=1; VNC_PHASE=1; VNC_OWNED=1
trap cleanup EXIT
exit 42
''')
        self.assertEqual(result.returncode, 2, result.stderr)
        calls = result.artifacts["calls"].decode()
        self.assertIn("disable --now tigervncserver@:1.service", calls)
        self.assertNotIn("disable --now tailscaled.service", calls)
        self.assertNotIn("stop ssh", calls)
        self.assertIn("PARTIAL FAILURE", result.stdout)
        self.assertIn("VNC_CURRENT_LOG", result.stdout)
        self.assertIn("VNC_JOURNAL", result.stdout)
        self.assertLess(calls.index("status"), calls.index("disable --now"))
        self.assertIn("sudo ares-enable-remote-access", result.stdout)

    def test_socket_activated_baseline_does_not_enable_service_and_restores_pair(self):
        result = shell("ares_enable_remote_access.sh", SYSTEMD_FIXTURE + '''
capture_ssh_baseline "$STATE_DIR/ssh-before.conf"
ensure_ssh
ACTIVE[ssh.service]=yes # Incoming socket-activated SSH started the service.
restore_ssh_baseline "$STATE_DIR/ssh-before.conf"
[[ "${ACTIVE[ssh.socket]}" == yes && "${ENABLED[ssh.socket]}" == enabled ]]
[[ "${ACTIVE[ssh.service]}" == no && "${ENABLED[ssh.service]}" == disabled ]]
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("enable --now ssh.service", result.artifacts["calls"].decode())
        saved = result.artifacts["ssh-before.conf"].decode()
        self.assertIn("SSH_SERVICE_ACTIVE=no", saved)
        self.assertIn("SSH_SOCKET_ACTIVE=yes", saved)
        self.assertIn("SSH_SOCKET_ENABLED=enabled", saved)

    def test_activation_owned_ssh_socket_restored_and_original_baseline_not_overwritten(self):
        result = shell("ares_enable_remote_access.sh", SYSTEMD_FIXTURE + '''
ACTIVE[ssh.socket]=no; ENABLED[ssh.socket]=disabled
capture_ssh_baseline "$STATE_DIR/ssh-before.conf"
ensure_ssh
capture_ssh_baseline "$STATE_DIR/ssh-before.conf"
restore_ssh_baseline "$STATE_DIR/ssh-before.conf"
[[ "${ACTIVE[ssh.socket]}" == no && "${ENABLED[ssh.socket]}" == disabled ]]
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("enable --now ssh.socket", result.artifacts["calls"].decode())
        self.assertIn("SSH_SOCKET_ACTIVE=no", result.artifacts["ssh-before.conf"].decode())

    def test_service_only_baseline_and_legacy_migration(self):
        result = shell("ares_enable_remote_access.sh", SYSTEMD_FIXTURE + '''
PRESENT[ssh.socket]=no; ACTIVE[ssh.socket]=no
ACTIVE[ssh.service]=yes; ENABLED[ssh.service]=enabled
printf 'SSH_WAS_ACTIVE=no\nSSH_WAS_ENABLED=no\n' > "$STATE_DIR/ssh-before.conf"
capture_ssh_baseline "$STATE_DIR/ssh-before.conf"
restore_ssh_baseline "$STATE_DIR/ssh-before.conf"
[[ "${ACTIVE[ssh.service]}" == no && "${ENABLED[ssh.service]}" == disabled ]]
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ssh-before.conf.v1", result.artifacts)

    def test_runtime_enablement_kind_and_static_service_baseline_are_preserved(self):
        result = shell("ares_enable_remote_access.sh", SYSTEMD_FIXTURE + '''
ENABLED[ssh.service]=static
ENABLED[ssh.socket]=enabled-runtime
capture_ssh_baseline "$STATE_DIR/ssh-before.conf"
ENABLED[ssh.socket]=enabled
ACTIVE[ssh.service]=yes
restore_ssh_baseline "$STATE_DIR/ssh-before.conf"
[[ "${ENABLED[ssh.socket]}" == enabled-runtime && "${ENABLED[ssh.service]}" == static ]]
[[ "${ACTIVE[ssh.service]}" == no && "${ACTIVE[ssh.socket]}" == yes ]]
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("enable --runtime ssh.socket", result.artifacts["calls"].decode())

    def test_saved_ssh_baseline_is_data_and_does_not_execute_shell_text(self):
        result = shell("ares_enable_remote_access.sh", '''
printf 'SSH_STATE_VERSION=2\nSSH_SOCKET_ACTIVE=$(touch unexpected)\n' > "$STATE_DIR/ssh-before.conf"
if load_ssh_baseline "$STATE_DIR/ssh-before.conf"; then exit 1; fi
[[ ! -e unexpected ]]
''')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_disable_restores_socket_baseline_and_retains_identity_files(self):
        result = shell("ares_disable_remote_access.sh", SYSTEMD_FIXTURE + '''
capture_ssh_baseline "$STATE_DIR/ssh-before.conf"
ACTIVE[ssh.service]=yes; ACTIVE[tigervncserver@:1.service]=yes
ss() { :; }
disable_remote_services
[[ "${ACTIVE[tailscaled.service]}" == no && "${ACTIVE[tigervncserver@:1.service]}" == no ]]
[[ "${ACTIVE[ssh.socket]}" == yes && "${ENABLED[ssh.socket]}" == enabled ]]
[[ "${ACTIVE[ssh.service]}" == no && "${ENABLED[ssh.service]}" == disabled ]]
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ssh-before.conf", result.artifacts)
        self.assertIn("identity", result.stdout)

    def test_vnc_config_and_per_user_startup_are_generated_without_console_session_changes(self):
        result = shell("ares_enable_remote_access.sh", SYSTEMD_FIXTURE + r'''
WORK="$STATE_DIR/work"; TARGET_HOME="$STATE_DIR/home"
VNC_USERS_FILE="$STATE_DIR/etc/vncserver.users"
mkdir -p "$WORK" "$TARGET_HOME/.vnc"
printf 'ENCODED8' > "$TARGET_HOME/.vnc/passwd"
ss() { :; }
chown() { :; }
tigervncpasswd() { :; }
tigervncserver() { :; }
runuser() { :; }
journalctl() { :; }
dbus-run-session() { :; }
cinnamon-session-cinnamon2d() { :; }
install() {
  if [[ "$1" == -d ]]; then mkdir -p "${@: -1}"; else cp "${@: -2:1}" "${@: -1}"; fi
}
configure_vnc
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        value = result.artifacts["home/.vnc/tigervnc.conf"].decode()
        self.assertIn('$AlwaysShared = "yes";', value)
        self.assertNotIn("$alwaysShared", value)
        self.assertIn('Xtigervnc-session', value)
        startup = result.artifacts["home/.vnc/Xtigervnc-session"].decode()
        self.assertIn("exec dbus-run-session -- cinnamon-session-cinnamon2d", startup)
        self.assertNotIn("pkill", startup)
        self.assertNotIn("killall", startup)
        self.assertEqual(result.artifacts["home/.vnc/passwd"], b"ENCODED8")

    def test_vnc_requires_three_consecutive_healthy_samples(self):
        result = shell("ares_enable_remote_access.sh", SYSTEMD_FIXTURE + '''
HEALTH=0
sleep() { :; }
verify_vnc_listeners() { HEALTH=$((HEALTH + 1)); [[ "$HEALTH" -ne 2 ]]; }
start_vnc
[[ "$HEALTH" -eq 5 ]]
''')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_conflicting_display_owner_is_not_stopped_by_partial_failure_cleanup(self):
        result = shell("ares_enable_remote_access.sh", SYSTEMD_FIXTURE + '''
WORK="$STATE_DIR/work"; TARGET_HOME="$STATE_DIR/home"; mkdir -p "$WORK"
VNC_USERS_FILE="$STATE_DIR/users"; printf ':1=another-user\n' > "$VNC_USERS_FILE"
journalctl() { :; }
print_ssh_instructions() { :; }
ACTIVE[tigervncserver@:1.service]=yes
STARTED=1; CLI_READY=1; VNC_PHASE=1
trap cleanup EXIT
configure_vnc || exit 1
''')
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("disable --now", result.artifacts["calls"].decode())
        self.assertIn("ownership is unresolved", result.stderr)

    def test_optional_partial_result_preserves_core_success(self):
        result = shell("optional_remote_support.sh", '''
function /usr/local/sbin/ares-enable-remote-access() { return 2; }
run_optional_remote_support y
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Tailscale and SSH remain operational", result.stdout)
        self.assertIn("core installation remains successful", result.stdout)

    def test_password_prompts_matching_bounds_single_filtered_record_and_no_secret_output(self):
        for values, succeeds in (("Abc123!\nAbc123!\n", True),
                                  ("abcdef\nabcdef\n", True),
                                  ("abcdefgh\nabcdefgh\n", True),
                                  ("short\nshort\n" * 3, False),
                                  ("123456789\n123456789\n" * 3, False),
                                  ("Abc123!\nDifferent\n" * 3, False)):
            escaped = values.replace("\n", "\\n")
            code = r'''
WORK="$STATE_DIR/work"; TARGET_HOME="$STATE_DIR/home"; mkdir -p "$WORK" "$TARGET_HOME"
exec 3>"$STATE_DIR/terminal"
runuser() {
  [[ "${@: -2}" == 'tigervncpasswd -f' ]] || return 1
  local first second; IFS= read -r first
  if IFS= read -r second; then return 1; fi
  printf 'ENCODED8'
}
install() { cp "${@: -2:1}" "${@: -1}"; }
''' + "exec 4<<<$'" + escaped + "'\ncreate_vnc_password \"$STATE_DIR/password\""
            result = shell("ares_enable_remote_access.sh", code)
            self.assertEqual(result.returncode == 0, succeeds, result.stderr)
            self.assertNotIn("Abc123!", result.stdout + result.stderr)
            self.assertNotIn(b"Abc123!", result.artifacts["terminal"])
            self.assertIn(b"Re-enter TigerVNC password to confirm", result.artifacts["terminal"])
            if succeeds:
                self.assertEqual(result.artifacts["password"], b"ENCODED8")
            else:
                self.assertNotIn("password", result.artifacts)

    def test_tailscale_enrollment_url_uses_unlogged_terminal_and_timeout_is_finite(self):
        code = r'''
exec 3>"$STATE_DIR/terminal"; exec 4<<<'y'
exec 5>&1 6>&2
exec > >(python3 -u "$CONFIG_TOOL" redact | tee "$STATE_DIR/activation.log") 2>&1
logger=$!
timeout() { echo "$*" >> "$STATE_DIR/timeouts"; while [[ "$1" != tailscale ]]; do shift; done; "$@"; }
tailscale_connected() { [[ -f "$STATE_DIR/connected" ]]; }
tailscale() {
  case "$1" in up) echo 'https://login.tailscale.com/a/TEST_ONLY'; touch "$STATE_DIR/connected" ;; set) return 0 ;; esac
}
enroll_tailscale test-school
printf 'Diagnostic https://login.tailscale.com/a/DIAGNOSTIC_ONLY\n'
exec 1>&5 2>&6
wait "$logger"
'''
        result = shell("ares_enable_remote_access.sh", code)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("TEST_ONLY", result.stdout + result.stderr)
        self.assertIn(b"TEST_ONLY", result.artifacts["terminal"])
        self.assertNotIn(b"TEST_ONLY", result.artifacts["activation.log"])
        self.assertNotIn(b"DIAGNOSTIC_ONLY", result.artifacts["activation.log"])
        self.assertIn(b"[URL omitted]", result.artifacts["activation.log"])
        self.assertIn(b"125s tailscale up", result.artifacts["timeouts"])
        self.assertIn(b"--timeout=120s", result.artifacts["timeouts"])
        self.assertIn("cellular data", result.stdout)

    def test_deferred_offline_and_connected_retry_paths_do_not_reenroll_or_erase_identity(self):
        for mode in ("deferred", "offline", "connected"):
            code = r'''
exec 3>"$STATE_DIR/terminal"; exec 4<<<'y'
timeout() { while [[ "$1" != tailscale ]]; do shift; done; "$@"; }
tailscale() { echo "$*" >> "$STATE_DIR/tailscale-calls"; [[ "$1" != up ]]; }
''' + ('tailscale_connected() { return 0; }\n' if mode == "connected" else 'tailscale_connected() { return 1; }\n')
            if mode == "deferred":
                code += "exec 4<<<'N'\n"
            code += "enroll_tailscale test-school"
            result = shell("ares_enable_remote_access.sh", code)
            self.assertEqual(result.returncode, 0 if mode == "connected" else 3, result.stderr)
            calls = result.artifacts.get("tailscale-calls", b"").decode()
            self.assertNotIn("logout", calls)
            self.assertNotIn("down", calls)
            if mode != "offline":
                self.assertNotIn("up ", calls)
            if mode != "connected":
                self.assertIn("sudo ares-enable-remote-access", result.stdout)

    def test_url_redaction_and_connected_status_checks(self):
        for state, ok in (({"BackendState": "Running", "Self": {"Online": True}}, True),
                          ({"BackendState": "Running", "Self": {"Online": False}}, False),
                          ({"BackendState": "NeedsLogin"}, False)):
            import json
            result = subprocess.run([sys.executable, "-B", str(BUILDER / "tools/remote_support_config.py"), "connected"],
                                    input=json.dumps(state), capture_output=True, text=True)
            self.assertEqual(result.returncode == 0, ok)
        result = subprocess.run([sys.executable, "-B", str(BUILDER / "tools/remote_support_config.py"), "redact"],
                                input="Diagnostic https://login.tailscale.com/a/TEST_ONLY retained\n", capture_output=True, text=True)
        self.assertEqual(result.stdout, "Diagnostic [URL omitted] retained\n")

    def test_private_vnc_route_rejects_foreground_public_tls_and_other_targets(self):
        route = {'TCPForward': '127.0.0.1:5901'}
        for value, expected in (
                (None, 'absent'), ({}, 'absent'),
                ({'TCP': {'443': {'HTTPS': True}}}, 'absent'),
                ({'TCP': {'5901': route, '443': {'HTTPS': True}}}, 'configured'),
                ({'TCP': {'5901': {'TCPForward': '127.0.0.1:9999'}}}, 'conflict'),
                ({'TCP': {'5901': dict(route, TerminateTLS='school.test.ts.net')}}, 'conflict'),
                ({'TCP': {'5901': route}, 'AllowFunnel': {'school.test.ts.net:5901': True}}, 'conflict'),
                ({'Foreground': {'session': {'TCP': {'5901': route}}}}, 'conflict')):
            with self.subTest(value=value):
                self.assertEqual(config.vnc_route(value), expected)
        with self.assertRaises(ValueError):
            config.vnc_route([])

    def test_private_vnc_forwarding_is_persistent_and_rerun_reuses_existing_route(self):
        result = shell('ares_enable_remote_access.sh', r'''
printf '{"TCP":{"443":{"HTTPS":true}}}' > "$STATE_DIR/serve.json"
timeout() { shift; "$@"; }
tailscale() {
  echo "$*" >> "$STATE_DIR/tailscale-calls"
  if [[ "$*" == 'serve status --json' ]]; then cat "$STATE_DIR/serve.json"; return; fi
  [[ "$*" == 'serve --bg --yes --tcp=5901 tcp://127.0.0.1:5901' ]] || return 1
  printf '{"TCP":{"443":{"HTTPS":true},"5901":{"TCPForward":"127.0.0.1:5901"}}}' > "$STATE_DIR/serve.json"
}
configure_vnc_route
configure_vnc_route
''')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        calls = result.artifacts['tailscale-calls'].decode()
        self.assertEqual(calls.count('serve --bg --yes --tcp=5901'), 1)
        self.assertNotIn('reset', calls)
        import json
        self.assertEqual(json.loads(result.artifacts['serve.json'])['TCP']['443'], {'HTTPS': True})

    def test_route_conflict_or_failed_configuration_does_not_replace_existing_settings(self):
        for conflict in (True, False):
            before = '{"TCP":{"5901":{"TCPForward":"127.0.0.1:9999"}}}' if conflict else '{}'
            result = shell('ares_enable_remote_access.sh',
                           "printf '%s' '" + before + "' > \"$STATE_DIR/serve.json\"\n" + r'''
timeout() { shift; "$@"; }
tailscale() {
  echo "$*" >> "$STATE_DIR/tailscale-calls"
  if [[ "$*" == 'serve status --json' ]]; then cat "$STATE_DIR/serve.json"; else return 1; fi
}
configure_vnc_route
''')
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.artifacts['serve.json'].decode(), before)
            if conflict:
                self.assertNotIn('--bg', result.artifacts['tailscale-calls'].decode())

    def test_private_route_failure_preserves_healthy_vnc_and_ssh(self):
        result = shell('ares_enable_remote_access.sh', SYSTEMD_FIXTURE + '''
STARTED=1; CLI_READY=1; VNC_PHASE=1; VNC_OWNED=1; VNC_READY=1
ACTIVE[tigervncserver@:1.service]=yes
print_ssh_instructions() { :; }
trap cleanup EXIT
exit 1
''')
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('SSH and local TigerVNC remain running', result.stdout)
        self.assertNotIn('disable --now', result.artifacts.get('calls', b'').decode())

    def test_connection_summary_reports_actual_health_and_omits_authentication_urls(self):
        import json
        value = {'BackendState': 'Running', 'Self': {'Online': False},
                 'Health': ['Cannot synchronize; visit https://login.tailscale.com/a/TEST_ONLY']}
        result = subprocess.run([sys.executable, '-B', str(BUILDER / 'tools/remote_support_config.py'), 'connection-summary'],
                                input=json.dumps(value), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Coordination connection: offline', result.stdout)
        self.assertIn('Cannot synchronize', result.stdout)
        self.assertNotIn('TEST_ONLY', result.stdout)

    def test_ready_instructions_offer_saved_viewer_connection(self):
        result = shell('ares_enable_remote_access.sh', '''
exec 3>"$STATE_DIR/terminal"
timeout() { echo 100.64.0.99; }
COMPLETE=1
print_ssh_instructions
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        terminal = result.artifacts['terminal'].decode()
        self.assertIn('100.64.0.99::5901', terminal)
        self.assertNotIn('ssh -N', terminal)

    def test_optional_decline_and_failure_preserve_core_success(self):
        for reply in ("", "N", "y"):
            code = '''function /usr/local/sbin/ares-enable-remote-access() { echo CALLED; return 7; }
run_optional_remote_support "''' + reply + '"'
            result = shell("optional_remote_support.sh", code)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("core installation remains successful", result.stdout)
            self.assertEqual("CALLED" in result.stdout, reply == "y")


if __name__ == "__main__":
    unittest.main()
