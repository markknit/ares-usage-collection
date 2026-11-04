# AnyDesk identity for each school

AnyDesk must already be installed in the approved Ubuntu base. This setup does
not download or update the AnyDesk application. It personalizes the installed
client after cloning the school image.

The master installer prepares these commands and offers setup after the core
installation succeeds. Use a local console or independent SSH connection:

```bash
sudo ares-setup-anydesk ARES-S00XX
```

Use the school's assigned code. At the first setup, type `RESET` to confirm the
identity change, then enter and confirm the standard ARES unattended-access
password. Input is hidden. No password is embedded in Git, arguments, receipts
or the installation log. An empty response defers setup and keeps the old ID.

The helper stops AnyDesk and closes its remaining GUI processes, archives the
installed `/etc/anydesk` configuration (including both `system.conf` and
`service.conf`) and the invoking desktop user's `.anydesk` configuration when
present, then enables/starts the AnyDesk service. The old files are retained in
root-only `/var/lib/ares/anydesk-setup/backup-*/`. Resetting disconnects existing
AnyDesk sessions and replaces identity/settings from the cloned base.

The supported `anydesk --set-password` command sets unattended access. The helper
queries `anydesk --get-id`, requires a numeric ID different from the recorded
old ID, displays it and saves it at:

```text
/var/lib/ares/anydesk-setup/anydesk-id.txt
```

Save that ID with the school's support record. Show it again later with:

```bash
sudo ares-show-anydesk-id
```

If disconnected AnyDesk cannot return a new ID, it reports **Pending** and leaves
the reset recorded. Retry after AnyDesk has a usable connection; an ordinary
retry does not reset the identity again. A failed password command also remains
Pending; rerun `ares-setup-anydesk` and enter the password again. After successful
setup, an ordinary installer rerun preserves both identity and password. A
deliberate replacement requires `ares-setup-anydesk --reset ARES-S00XX` and the
same local confirmation. A different school code requires that explicit reset.

## Desktop client and SSH setup

The AnyDesk background service reporting online and returning an ID is not proof
that its graphical client can capture the desktop. An incoming Linux connection
needs a usable Xorg desktop. After reset, the helper selects the existing local
X11 session, repairs ownership of `ares`'s `.anydesk` folder and launches the
client as `ares` using that session's actual DISPLAY/Xauthority. It does not
assume display :0, restart the display manager, create another desktop or change
the AnyDesk ID/password during client recovery.

Root CLI queries/password setup use root's HOME and omit desktop environment
variables, to avoid creating root-owned files in the user's profile. The global
`/etc/anydesk` configuration remains root-owned; only the desktop user's folder
belongs to `ares`. If no unique X11 session exists or the graphical process
immediately aborts, setup reports Pending and preserves the new ID/password.
A client launch is still not an accepted unattended connection test.

To recover only the client from SSH, after logging into the local Xorg desktop:

```bash
sudo ares-recover-anydesk-desktop
```

Its log is `/var/log/ares-anydesk-desktop.log`. Do not repeatedly reset a valid
new ID to troubleshoot a desktop IPC error. The November 4 operator report
showed a root-owned user profile and a client abort; correcting ownership and
launching the client did not by itself establish recovery. A reboot/retest was
requested, and live recovery remains Pending until the operator confirms it.

Existing active or boot-enabled Internet Lockdown defers AnyDesk setup, because
restarting its service could invalidate service-specific firewall allowances.
Arrange local access and restore/disable lockdown before retrying. The helper
does not change the firewall or claim unattended connection acceptance from a
successful password command; test an actual AnyDesk connection separately.

Reference: [AnyDesk's Linux CLI](https://support.anydesk.com/docs/command-line-interface-for-linux)
and [cloned-system guidance](https://support.anydesk.com/docs/back-up-anydesk-id-and-settings).
