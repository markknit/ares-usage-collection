# Preserve tsavo3 before the full offline-install test

A whole-disk Clonezilla restore erases Ubuntu and the data partition. On the
inspected tsavo3 layout, Ubuntu is on `/dev/sda2` and `/mnt/sda3` is an alias for
the `/dev/sda3` mount. The data partition is on the same physical disk.

The owner will restore an existing Clonezilla image of this same system without
the offline-installer additions. That image supplies the unchanged base system
and school content library. Keep the Clonezilla image off tsavo3 and available
before starting. Its contents and restorability have not been independently
verified by this installer project.

## Keep off the server before reloading

- The corrected, independently verified v1.13 installer ZIP, its checksum and
  the technician overview. Also retain the older verified ZIP as a fallback.
- The original/normalized build source and sealed evidence directory, including
  the inheritance policy, original inventory and approval records. GitHub holds
  code and documentation; it does not hold these media/build inputs by itself.
- Installation/build logs and any changes saved outside the installer-managed
  locations since the Clonezilla image was made.
- A private configuration backup: school identity, Nginx/admin authentication,
  network setup, local support scripts/services and existing support identities.
- A current Lesson3 database dump, private deployment `.env` and any needed
  generated artifacts. These contain the Site Administrator, users and edits;
  the installer can recreate the supplied corpus but not later user changes.
- Current admin/module pages, ARES Sync usage/tracker data and other unique local
  content. The approved supplied pages/manual are also retained in the repository.

The build archive and private backup must be copied to Windows or an external
drive and their checksums confirmed before reload. A backup still on `/mnt/sda3`
will be erased with that partition. Treat configuration, SSH/Tailscale/AnyDesk
state and database archives as private; do not put them in GitHub or send them
with the technician overview.

## Clean-test boundary

Use the clean Clonezilla base plus the corrected ZIP for the installation test.
For first-school identity tests, the reusable base must predate AnyDesk school
personalization and must not contain its completed
`/var/lib/ares/anydesk-setup/` record. A full reinstall on an already personalized
server intentionally retains its ID. See `docs/ANYDESK_SETUP.md` for deliberate
reassignment or an image that already contains school-specific support state.
Do not automatically restore old `/etc`, firewall rules, private support state
or a working Lesson3 database onto it: that would mix the old installation into
the clean test. Retain backups for recovery or deliberate data migration.

The preservation helper captures known configuration, database and changed page
locations without restarting services or changing firewall rules. It is not a
full-disk image or a backup of every school-library directory. Unchanged library
coverage depends on the owner's existing Clonezilla image; save any other unique
files separately. A successful archive/copy check is not a completed restore test.
