# Owner-approved admin content

These three files were supplied and reported tested by the owner on 2026-11-01.
Keep their bytes unchanged; do not render, normalize or regenerate the PDF.

| Supplied file | Packaged name | Destination |
|---|---|---|
| `admin_temp.html` | `admin.html` | `/mnt/sda3/var/www/admin/admin.html` |
| `index_temp.htmlf` | `index.htmlf` | `/mnt/sda3/var/www/modules/Admin_tools/index.htmlf` |
| `ARES_Sync_User_Guide.pdf` | `ARES_Sync_User_Guide.pdf` | `/mnt/sda3/var/www/admin/ARES_Sync_User_Guide.pdf` |

The owner's `/mt/sda3` PDF destination was interpreted as `/mnt/sda3`, matching
the other destinations and the actual ARES storage layout. The admin page's
relative manual link therefore remains inside the password-protected folder.

The builder packages these files under `teacher-app/admin-content/`, covered by
the existing component and root inventories. The teacher-app stage invokes
`install_admin_content.sh` once to deploy the group. It requires the existing
destination directories, backs up prior files to a private timestamped folder
under `/var/backups/ares-admin-content/`, preserves existing file modes and
ownership, and does not edit directory permissions or authentication settings.
New files default to mode 0644 and ownership `ares:www-data`.

Only these three named payload files are packaged; this provenance note is not
part of the deployed content. This is a content update, not a service change.
The files were not functionally retested after the owner's approval.
