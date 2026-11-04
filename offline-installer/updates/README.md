# Historical November 3 offline update

This retained ZIP predates the November 4 remote-support/AnyDesk corrections.
Use the newest full installer for further testing. The source packager now
includes the desktop-client recovery helper and updated activation controls.

Use `ARES_v1.13_School_Setup_Update_20261103.zip` to apply just the school
hostname/generic alias, disconnected-safe lockdown command and AnyDesk cloning
updates. It does not rerun Lesson3/content installation or database imports.

Copy the ZIP to the server by USB or LAN and extract it into a fresh folder.
In a normal Ubuntu terminal at the local console, run:

```bash
sudo bash apply_school_setup_updates.sh ARES-S0035
```

Use the school's assigned code at other sites. The package checks itself.
AnyDesk setup asks for `RESET` and the standard unattended password twice;
reset stops AnyDesk and disconnects existing sessions. Save the new ID, or
follow the included guide if it remains Pending. Retrying preserves the new
identity. Existing active/boot lockdown defers incompatible service changes.
The update does not activate firewall rules or enable boot lockdown.

Source: `96281fc50741e539f1f3131c9dd4265abcb4a2bc`.
Archive: 120,940 bytes; 29 independently extracted/checksummed files.
SHA-256: `7e823b05657ca92342f76508f53f15d0a65ce591765ceddda4cd147105f2a561`.

The refreshed full installer ZIP is separately retained on Windows for future
fresh installations. Exact identity and verification are in
[the release evidence](../docs/evidence/2026-11-03-school-setup-update.md).
New live acceptance remains Pending.
