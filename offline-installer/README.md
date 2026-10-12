# ARES Q4 Offline Installer Builder v1.11

This kit converts the approved ARES Q4 update folder into a field package that can be installed at a school with **no Internet connection**.

## v1.11 changes

- Pins the official Lesson3 `v0.94` release and its immutable container-image references.
- Adds Lesson3 Discussions for signed-in teachers. Discussions are enabled by default and remain
  local to each school's Lesson3 database; a Site Administrator can disable or moderate them.
- Retains the field-tested fresh-install corpus workflow: 95 JSON plans are uploaded in two
  authenticated batches and verified as 806 lessons. The new administrator ZIP-upload feature is
  available for later managed content updates but is not substituted into the installer.
- Refreshes the bundled Lesson3 User Guide for Discussions, ZIP uploads, and administrator controls.
- Produces a separately versioned v1.11 field package. Retain v1.10 as the known-good fallback until
  v1.11 completes offline field acceptance.

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

  `http://ares.local/app_install/`

- The direct APK remains:

  `http://ares.local/downloads/ares-sync.apk`

- Updated technician and teacher guides are included in the field bundle under `docs/`.

- The complete Lesson3 User Guide is bundled with the field package, installed on the ARES server, and linked from the Lesson Plan Editor interface.
- The offline guide is published at:

  `http://ares.local/modules/Lesson_Plans/LESSON3_USER_GUIDE.pdf`

## Included

- Lesson Plan module/PDF deployment
- `ares.local` mDNS/Nginx setup
- Lesson3 Lesson Plan Editor on port 3001
- Lesson Plan tracker key mappings
- ARES Sync / usage-collection server update
- approved ARES Sync teacher APK + local `/app_install/` page
- package SHA-256 verification, preflight, post-install checks, and logging
- technician and teacher setup guides
- approved Lesson3 JSON corpus plus fresh-database installer and rollback
- dormant Tailscale and TigerVNC packages for later activation
- safe school-code reassignment command for provisional installations

## Intentionally excluded

- Tsavo Trust module (use its separately reviewed installer)
- Xpra
- automatic Tailscale registration or remote-access activation

## Build machine requirements

Use an Internet-connected Ubuntu 24.04 AMD64 machine with Docker Engine + Docker Compose v2 and
the normal command-line tools (`curl`, `git`, `rsync`, `gzip`, `sha256sum`, `tar`, `python3`,
`apt-get`, and `dpkg-deb`). The target bundle contains `linux/amd64` images and offline remote-access
packages for Intel ARES school servers.

## Normal build

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
cd ARES_Q4_Offline_v0.94_amd64_v1.11
sudo bash preflight.sh ARES-S00XX
sudo bash install_offline.sh ARES-S00XX
```

Do not proceed if preflight reports `NOT READY`.

The installer creates Lesson3, then pauses when the first Site Administrator must be created:

1. Open `http://ares.local:3001/login` and create the first Site Administrator.
2. Return to the still-running installer and type `READY`.
3. Enter that Site Administrator's credentials when prompted.

The same `install_offline.sh` process then creates a rollback snapshot, imports the two required API
batches, and verifies the final 95 plans / 806 lessons. It runs only against an empty Lesson3
content database and will not silently revise or overwrite lesson plans already present at a school.

The installation also prepares Tailscale and TigerVNC without enabling or registering either one.
See `docs/REMOTE_ACCESS.md` before later running `sudo ares-enable-remote-access`.

After successful installation, a teacher connected to ARES/ARES2 can install the app locally from:

`http://ares.local/app_install/`

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

## Scaffold mode

For development/testing only:

```bash
bash build_offline_bundle.sh --source ... --output ... --scaffold-only
```

Scaffold mode deliberately omits Lesson3 release/images and the APK and writes `NOT_FIELD_READY.txt`. Do not send scaffold output to a school.
