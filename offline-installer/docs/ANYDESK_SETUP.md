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

Existing active or boot-enabled Internet Lockdown defers AnyDesk setup, because
restarting its service could invalidate service-specific firewall allowances.
Arrange local access and restore/disable lockdown before retrying. The helper
does not change the firewall or claim unattended connection acceptance from a
successful password command; test an actual AnyDesk connection separately.

Reference: [AnyDesk's Linux CLI](https://support.anydesk.com/docs/command-line-interface-for-linux)
and [cloned-system guidance](https://support.anydesk.com/docs/back-up-anydesk-id-and-settings).
