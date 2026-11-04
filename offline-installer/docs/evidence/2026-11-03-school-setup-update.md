# November 3 standalone installation follow-up

## Operator report and scope

The owner reports that the standalone, no-Internet installation on a newly
loaded ARES server ran well except that the generic mDNS name was missing and
lockdown setup required an active network adapter. The owner also requested
AnyDesk identity reset/unattended setup for each cloned school server.

No new installation transcript or service journal was supplied with that report;
the exact host-side cause of the missing alias has not been established. The
source was already intended to preserve the machine hostname and add the generic
alias, rather than deliberately suppressing it because another server exists.

## Implemented in source 96281fc

Full commit: `96281fc50741e539f1f3131c9dd4265abcb4a2bc`, published on
`simplify-offline-install`.

- Preserve Avahi's school `hostname.local`; add the selected generic profile
  alias and both Nginx names without renaming Linux. The publisher waits for
  addresses, accepts a link-local IPv4 LAN, follows changes and retries exited
  publishers. A shared name still cannot unambiguously identify two servers on
  one LAN; the test profile retains its separate `ares-test.local` alias.
- Install lockdown/restore commands even when disconnected or noninteractive.
  Select the actual student-facing IPv4 interface/subnet on first activation;
  do not automatically bless a modem-only uplink. Restore needs no LAN selection.
  Original v1.4.2 release/rule bytes are unchanged. Installation activates no
  firewall and enables no boot lockdown. Active/boot lockdown preserves its
  existing runtime/configuration and defers service-changing work.
- Add an AnyDesk helper for the already-installed base client. After local
  `RESET` confirmation, stop AnyDesk, close remaining clients, archive installed
  and invoking-user settings, then enable/start the service. Both `system.conf`
  and `service.conf` are archived, matching the vendor's cloned-system guidance.
  Configure the hidden unattended password through the supported CLI and
  display/save a valid new ID different from the recorded old ID. Pending ID or
  password work retries without another reset. Ordinary completed reruns preserve
  identity/password; different-school or deliberate resets are explicit.

No password is hardcoded, committed or passed as a process argument. Neither
the password command's exit status nor a reported ID is claimed as an accepted
live unattended connection. Active/boot lockdown prevents AnyDesk service reset
until separately arranged safe recovery. No new server access was established,
and no actual AnyDesk reset, firewall activation or service restart was run here.

## Verification

- Native Ubuntu CI passed **104 tests** and installer shell syntax checks:
  https://github.com/markknit/ares-usage-collection/actions/runs/41762656344
  (job `126353687959`). Coverage includes publisher retry, both Nginx profiles,
  unplugged command installation, first-use LAN validation, AnyDesk reset,
  pending/retry/deferral/password handling, master optional-failure behavior,
  full bundle verification and the small update archive.
- Focused portable suite passed 44 tests; final AnyDesk preflight and guide
  checksum refresh were checked again. Two updated PDFs were rendered and all
  six pages visually reviewed. Delivered PDF page renderings match those reviewed.
- Packaging used a canonical committed export with Windows newline conversion
  disabled. The first preflight correctly rejected the working-copy source-pin
  bytes before creating an output; the source pin or verifier was not bypassed.
- The actual full payload was independently extracted and verified on Windows:
  ZIP CRC/inventory, root and nested checksums, exact reviewed helpers, approved
  content, release/profile/APK, Docker image archives, corpus, Tsavo source/media,
  script syntax and offline audit passed. All four real DEB control archives
  were read through Windows system libarchive instead of the unavailable Linux
  `dpkg-deb` command; the same package/version/architecture assertions ran.
  Metadata reads are recorded in `windows-deb-metadata-verification.json`.
- ZIP Unix file modes are explicitly retained/generated, independent of NTFS.
  No installer, Docker pull/save/prune, payload download or server operation ran
  during packaging. Previous releases and private backups remain unchanged.

## Windows artifacts

Folder: `C:/Users/MRKni/Downloads/ARES_v1.13_Release_20261103/`.

Full ZIP:

- `ARES_Q4_Offline_v0.94_amd64_v1.13.zip`
- Size: 1,760,172,913 bytes; 340 independently verified files.
- SHA-256: `195a140f9acea56b7237b84e35a6853b3cb1a0939224db0060e456178a8372fe`.
- Reused 267 untouched original base files; updated/added 73 files.
- `repack-evidence.json`, checksum sidecar, `COMPLETED.txt`, packaging log,
  actual DEB metadata record and `WINDOWS_RELEASE_VERIFIED.json` retained.

Small update for the already-installed server:

- `ARES_v1.13_School_Setup_Update_20261103.zip`
- Size: 120,940 bytes; 29 independently extracted/checksummed files.
- SHA-256: `7e823b05657ca92342f76508f53f15d0a65ce591765ceddda4cd147105f2a561`.
- Exact ZIP and sidecar also retained under `offline-installer/updates/` in Git.

`START_HERE.txt` distinguishes the small update from the full fresh-install ZIP.
The Documents folder includes the revised two-page overview, four-page technician
guide, teacher guide, approved user manual and original lockdown PDF. PDF copies
match their full-ZIP entries. The full ZIP remains outside GitHub because of its
size; source, the small update and release evidence are published in the branch.

## Next live check

Apply the small update from a local Ubuntu terminal with
`sudo bash apply_school_setup_updates.sh ARES-S0035`; other schools use their
assigned code. Verify both names from another LAN client, check later lockdown
selection/restore with safe access, and save/test the new AnyDesk ID and
unattended connection. These new live checks remain **Pending**.
