# ARES Q4 Offline Installer Builder v1.13

## Corrected v1.13 packaging and technician handoff

The current source includes the storage-alias fix, direct phone-page link,
approved admin pages/manual and Internet Lockdown v1.4.2. The two-page
`docs/TECHNICIAN_OVERVIEW.md` and generated
`docs/pdf/ARES_Offline_Installer_Overview.pdf` summarize the components and normal
technician process. `docs/PRE_RELOAD_PRESERVATION.md` covers the separate backup
step before a whole-disk Clonezilla restore.

`repackage_verified_v113.py` refreshes only the known, previously verified
production ZIP (SHA-256 beginning `1f0993a8`) using the current reviewed source.
It reuses the bundled APK, Docker images, media and corpus without downloads,
Docker operations or an installer run. It requires a fresh output directory,
checks untouched base files, regenerates guides/checksums and independently
extracts/verifies the candidate before promoting the corrected ZIP. The original
ZIP and its evidence remain unchanged. The old `--resume` command was specific
to the original failed candidate and is not used for this corrected release.

This kit converts the approved ARES Q4 update folder into a field package that can be installed at a school with **no Internet connection**.

The builder now seals a production (`ares.local`, default) or permanent test
(`ares-test.local`) profile. See [profiles](docs/PROFILES.md), the
[reconciliation record](docs/RECONCILIATION.md), and the pending
[two-profile acceptance matrix](docs/PROFILE_ACCEPTANCE.md). Live target/client
acceptance has not been completed by the source changes. v1.13 includes validated
external-source TsavoTrust content; the legacy Tsavo installer and historical
checksum-bypass wrapper are excluded. Remote support uses standard OpenSSH over
Tailscale with Tailscale SSH explicitly disabled and a default-No activation prompt
after successful core installation. The connected build machine also requires
Python ReportLab to regenerate profile-specific printed rollout guides.

## v1.13 changes

- One technician command runs the package check, installation and functional checks.
  No manual checksum commands or checksum-bypass recovery choices are needed.
- The builder independently extracts and verifies its completed ZIP automatically.
  Detailed APK/profile, release/images, corpus, Tsavo and script checks run there.
  Component manifests remain available for release inspection and standalone utilities.
- Remote-support preparation runs after successful core installation. Missing
  desktop/SSH prerequisites or preparation failure report a warning and preserve
  core success. Routine offline installations decline optional activation.
- Makes optional remote activation finite and enrollment output terminal-only,
  preserves SSH service/socket baselines, and keeps working Tailscale/SSH after
  a TigerVNC failure. See [remote support](docs/REMOTE_ACCESS.md) for status codes,
  explicit hidden password prompts, retry and Pending lifecycle checks.
- Integrates Tsavo Trust from the normalized external build-source folder, pinned
  by exact filenames, sizes and SHA-256 hashes. Six MP4s remain outside Git.
- Adds transactional deployment, append-only tracking reconciliation and portal/
  HTTP range checks. See [Tsavo Trust](docs/TSAVO_TRUST.md) for the eight-file layout,
  backup/restore behavior and pending live acceptance gates.
- Root SHA256SUMS now covers nested checksum manifests while excluding only itself.
- Retains Lesson3 v0.94 and the verified v1.12 ZIP/evidence unchanged.

## v1.12 changes

- Pins the official Lesson3 `v0.94` release and its immutable container-image references.
- Adds Lesson3 Discussions for signed-in teachers. Discussions are enabled by default and remain
  local to each school's Lesson3 database; a Site Administrator can disable or moderate them.
- Retains the field-tested fresh-install corpus workflow: 95 JSON plans are uploaded in two
  authenticated batches and verified as 806 lessons. The new administrator ZIP-upload feature is
  available for later managed content updates but is not substituted into the installer.
- Refreshes the bundled Lesson3 User Guide for Discussions, ZIP uploads, and administrator controls.
- Produces a separately versioned v1.12 field package. Retain v1.10 as the known-good fallback until
  v1.12 completes offline field acceptance.

## v1.10 changes

- Replaces the stale ARES Sync files from the historic Q4 source folder with the reviewed rollout
  package embedded in this builder.
- Includes and validates the safe `ares-set-school-code` reassignment command.
- Refuses to build if the reassignment command is absent.
- Keeps the field installation to one command: the installer pauses for creation of the first
  Lesson3 Site Administrator, then imports and verifies the approved 95-plan/806-lesson corpus.
- Configures and verifies `ares.local` through the ARES server's existing Avahi service.
- Bundles pinned Tailscale and TigerVNC packages, installs them stopped and disabled, and provides
  separate activation/deactivation commands for a later authorized support session.
- Disables the base-image `x11vnc` service so it cannot remain exposed or conflict with the
  localhost-only TigerVNC configuration.

## v1.9 changes

- Corrects Lesson3 corpus uploads for JSON filenames containing commas.
- Prevents a transport-level upload failure from invoking the database rollback handler twice.
- Field-validated against Lesson3 v0.93 with all 95 plans and 806 lessons imported as Official
  version 1.0.0.

## v1.8 changes

- Pins the approved Lesson3 JSON corpus to Git commit
  `e07c243da77ad4554a2f404ae7790ef6e9d3e1b0` from
  `markknit/cbe-generation-system`.
- Validates and packages 95 lesson-plan files containing 806 lessons, with a manifest and exact
  SHA-256 checksums.
- Adds a fresh-database corpus installer that creates the 7 subjects and 8 subject-grade rows,
  uploads the corpus through Lesson3 v0.93's authenticated import API as batches of 50 and 45, and
  verifies the resulting database counts.
- Creates a pre-import PostgreSQL snapshot and automatically restores it if either batch or final
  verification fails.

## v1.7 changes

- Lesson3 is pinned to the tested `v0.93` release.
- The builder still verifies the release checksum published with the GitHub asset and now
  also confirms that the archive's internal `VERSION` matches the requested version before
  pulling or saving container images.

## v1.6 changes

- The approved production ARES Sync APK is automatically obtained by the Internet-connected builder from the ARES approval manifest in `markknit/ares-usage-collection`.
- The builder verifies the APK's exact approved SHA-256 and never falls back to debug or acceptance APK artifacts.
- The school server publishes a deliberately non-generic teacher installation page at:

  `http://ares.local/app_install/index.html`

- The direct APK remains:

  `http://ares.local/downloads/ares-sync.apk`

- Updated technician and teacher guides are included in the field bundle under `docs/`.

The same installation stage also deploys the owner's tested admin-content unit:
`admin/admin.html`, `modules/Admin_tools/index.htmlf` and
`admin/ARES_Sync_User_Guide.pdf` under `/mnt/sda3/var/www/`. Existing files are
backed up together, and the password-protected admin directory's configuration
and permissions are preserved. See [approved admin content](admin-content/README.md).

The complete supplied Internet Lockdown v1.4.2 project is also bundled, including
its original status, README, operating PDF and release manifest. After core setup,
the installer retains it under `/opt/ares/internet-lockdown/` and uses the supplied
installer's `--no-boot` mode. It does not activate firewall rules. Existing active
or boot-enabled lockdown and its remote services are preserved; setup is deferred
when needed without failing core ARES. See [Internet lockdown integration](docs/INTERNET_LOCKDOWN.md).

- The complete Lesson3 User Guide is bundled with the field package, installed on the ARES server, and linked from the Lesson Plan Editor interface.
- The offline guide is published at:

  `http://ares.local/modules/Lesson_Plans/LESSON3_USER_GUIDE.pdf`

## Included

- Lesson Plan module/PDF deployment
- `ares.local` mDNS/Nginx setup
- Lesson3 Lesson Plan Editor on port 3001
- Lesson Plan tracker key mappings
- ARES Sync / usage-collection server update
- approved ARES Sync teacher APK + local `/app_install/index.html` page
- package SHA-256 verification, preflight, post-install checks, and logging
- technician and teacher setup guides
- approved Lesson3 JSON corpus plus fresh-database installer and rollback
- dormant Tailscale and TigerVNC packages for later activation
- safe school-code reassignment command for provisional installations
- validated Tsavo Trust module, six offline videos and its tracking mapping

## Intentionally excluded

- legacy Tsavo Trust copy/link installer (replaced by the reviewed v1.13 module)
- Xpra
- automatic Tailscale registration or remote-access activation

## Build machine requirements

Use an Internet-connected Ubuntu 24.04 AMD64 machine with Docker Engine + Docker Compose v2 and
the normal command-line tools (`curl`, `git`, `rsync`, `gzip`, `sha256sum`, `tar`, `python3`,
`apt-get`, and `dpkg-deb`). The target bundle contains `linux/amd64` images and offline remote-access
packages for Intel ARES school servers.

## Normal build

For the already sealed tsavo3 C1 checkpoint, run from the new simplified-source
checkout:

```bash
bash offline-installer/run_tsavo3_build.sh
```

This machine-specific continuation preserves the old checkout and sealed source,
checks continuity, builds into a fresh hidden area, performs independent ZIP and
inherited-inventory verification, then promotes to `ARES_Q4_Update_offline_v1.13`
only after all checks pass. It refuses existing candidate/output paths, retains
failure logs and never runs an installer or prunes Docker. Do not reuse the old
C2 command block pinned to `728741b` for the simplified behavior.

If the simplified-r3 run created its ZIP but stopped at the saved-image archive
check, update this separate checkout to the shared-layer link correction and run:

```bash
bash offline-installer/run_tsavo3_build.sh --resume
```

Resume retains the original candidate ZIP and root manifest, checks the existing
staging tree, updates only the integrity helper, and reseals/repackages the same
payload. It performs no downloads, Docker pulls or image saves. All independent
checks and the inherited-file gate must pass before promotion; the original
normalized source, original build log and v1.12 artifact remain unchanged.

When the staged integrity helper is already current, resume reuses the existing
ZIP without changing its bytes. The inherited-file comparison reads that ZIP
directly and uses the same normalized newline convention as the B2 text approval
record. Other text changes and binary changes still fail; the report records
actual inherited-file hashes and identifies newline-normalized comparisons.

First provide exactly the normalized `TsavoTrust/` folder described in
[TSAVO_TRUST.md](docs/TSAVO_TRUST.md) within the external source. The builder fails
before replacing output if content is missing, nested, unexpected or unpinned.

```bash
sudo bash build_offline_bundle.sh \
  --source "/home/ares/Downloads/ARES_Q4_Update" \
  --output "/home/ares/Downloads/ARES_Q4_Update_offline"
```

The default Lesson3 release is pinned to `v0.94`.

### APK approval rule

Normal builds download `config/approved_apk.json` from the ARES GitHub repository. The manifest must identify package `org.areseducation.sync`, channel `production`, an approved download URL, and an exact SHA-256. The builder downloads the APK and refuses to continue if its SHA-256 differs.

Overrides are available only when deliberately needed:

```bash
--apk /path/to/approved/ares-sync.apk
```

or:

```bash
--apk-url "https://..." --apk-sha256 "64-hex-character-sha256"
```

## Field installation

Extract the completed field ZIP on the ARES server and run:

```bash
cd ARES_Q4_Offline_v0.94_amd64_v1.13
sudo bash install_offline.sh ARES-S00XX
```

Replace `ARES-S00XX` with the school's code. The installer checks the complete
package and server automatically before making installation changes. There is
no need to run preflight separately. If the package check fails, copy the complete
ZIP again and extract it into a new folder. For other failures, send ARES support
the installation log path printed on screen.

The installer creates Lesson3, then pauses when the first Site Administrator must be created:

1. Open `http://ares.local:3001/login` and create the first Site Administrator.
2. Return to the still-running installer and type `READY`.
3. Enter that Site Administrator's credentials when prompted.

The same `install_offline.sh` process then creates a rollback snapshot, imports the two required API
batches, and verifies the final 95 plans / 806 lessons. It runs only against an empty Lesson3
content database and will not silently revise or overwrite lesson plans already present at a school.

After core checks pass, the installation attempts to prepare dormant Tailscale
and TigerVNC, then offers activation if preparation succeeds. Preparation or
activation failure does not fail the completed offline installation. A prior
registration is retained.
See `docs/REMOTE_ACCESS.md` before later running `sudo ares-enable-remote-access`.

After successful installation, a teacher connected to ARES/ARES2 can install the app locally from:

`http://ares.local/app_install/index.html`

No Internet is required to download or install the APK. If the current enrollment flow needs to contact the central ARES enrollment service, normal Internet/mobile data is required when the one-time installation key is submitted.

## Field documentation

The completed field bundle includes:

- `docs/TECHNICIAN_PHONE_INSTALL.md`
- `docs/TEACHER_PHONE_GUIDE.md`
- `docs/pdf/ARES_Sync_Technician_Guide.pdf`
- `docs/pdf/ARES_Sync_Teacher_Guide.pdf`
- `docs/LESSON3_USER_GUIDE.pdf`
- `docs/LESSON3_CORPUS_INSTALL.md`
- `docs/LESSON3_V094_ACCEPTANCE.md`
- `docs/REMOTE_ACCESS.md`

The installed Lesson3 User Guide is also available locally from the Lesson Plan Editor area at `http://ares.local/modules/Lesson_Plans/LESSON3_USER_GUIDE.pdf`.

## Lesson3 offline method

The builder downloads the checksummed Lesson3 release and exact release images. At the school the installer loads those images locally, runs Lesson3 `--prepare-only`, and starts Compose with `--pull never`. No school-side Internet download is required.

GitHub remains the canonical source for the JSON corpus, not for a prebuilt PostgreSQL database.
The builder pins an exact approved corpus commit and packages its JSON. After the first Site
Administrator is created at a school, the guided step in `install_offline.sh` invokes the packaged
corpus installer to install the taxonomy and content through Lesson3's supported API with database
rollback protection.

For the update and acceptance procedure, see `docs/LESSON3_CORPUS_INSTALL.md`.

## Release verification (build staff)

The normal builder runs this automatically after creating the ZIP:

```bash
python3 verify_offline_bundle.py /path/to/ARES_Q4_Offline_v0.94_amd64_v1.13.zip
```

It uses a fresh extraction on the build disk and checks ZIP structure/CRC, complete
root inventory/checksums, component manifests, reviewed scripts, release/profile,
APK, image archives, 95 plans/806 lessons and the eight pinned Tsavo files/media.
It runs no installer or services. A failure stops the build; retain the candidate
for diagnosis and do not distribute it. Once it passes, identify the ZIP by its
printed hash and perform the offline installation and client checks on a disposable
server. Live installation and field acceptance remain Pending until performed.

## Scaffold mode

For development/testing only:

```bash
bash build_offline_bundle.sh --source ... --output ... --scaffold-only
```

Scaffold mode deliberately omits Lesson3 release/images and the APK and writes `NOT_FIELD_READY.txt`. Do not send scaffold output to a school.
