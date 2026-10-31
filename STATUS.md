# ARES Usage Collection Status

Last updated: 2026-10-30

## Current checkout

- Repository: `C:/dev/ares-usage-collection`.
- Branch: `production-baseline-cleanup`.
- Implementation tip reviewed: `973708935eacac62a210e7d065779090170733bf`.
- Approved Lesson3 release: v0.94; current source bundle revision: v1.13.
- Verified production artifact retained: v1.12 (identity and evidence below).
- Production alias: `ares.local`; permanent test alias: `ares-test.local`.
- This continuity record does not establish live deployment or field acceptance.

## Active Threads

| Thread | Status | Evidence / next action |
|---|---|---|
| Canonical release metadata and sealed profiles | Implemented; live acceptance pending | `785825f` records release configuration, profile rendering and Android endpoint changes. Verified with `git show --stat 785825f`. |
| Optional OpenSSH / TigerVNC support | Implemented; live acceptance pending | `3dccba4` records consolidated activation, failure cleanup and the optional post-core prompt. Verified with `git show --stat 3dccba4`. Real service, tunnel and desktop checks remain pending. |
| Manual TigerVNC component field test | Successful - user-reported; packaged acceptance Pending | See [2026-10-30 remote-access evidence](offline-installer/docs/evidence/2026-10-30-v1.12-remote-access-field-test.md). Packaged display `:1`, Tailscale-path SSH/VNC, reboot/autostart, disable/re-enable and failure cleanup remain Pending. |
| Compiled profile and guide validation | Software evidence recorded; live acceptance pending | `608cb7e` records compiled profile checks, guide rendering, alias audit, CI configuration and acceptance records. Verified with `git show --stat 608cb7e`; earlier software-test results are recorded in `offline-installer/docs/PROFILE_ACCEPTANCE.md`, not rerun by this documentation update. |
| Obfuscated APK policy resources | Fixed and locally validated; live acceptance pending | `verify_apk()` discovers compiled policies beneath `res/` using structural strings, ignores unparseable resources, and rejects missing/wrong/mixed policies. 27 local tests passed on 2026-10-30; approved production APK and both debug profiles pass verification. |
| Production profile live acceptance | Pending - all checks | Every production column entry in `offline-installer/docs/PROFILE_ACCEPTANCE.md` remains Pending. Requires an actual Ubuntu target, matching approved APK, phone and separate client evidence. |
| Permanent test profile live acceptance | Pending - all checks | Every permanent-test column entry in `offline-installer/docs/PROFILE_ACCEPTANCE.md` remains Pending. Includes actual discovery/collection and the Lesson3 UI/content gates. |
| Production v1.12 artifact | Built and independently verified; live acceptance Pending | `ARES_Q4_Offline_v0.94_amd64_v1.12.zip`, built from `973708935eacac62a210e7d065779090170733bf`; identity and verification evidence below. |
| TsavoTrust v1.13 integration | Implemented and software validated; live acceptance Pending | [Tsavo Trust](offline-installer/docs/TSAVO_TRUST.md): pinned external eight-file input, corrected page, transactional deployment, append-only mapping and HTTP range verification. 45 tests passed, one native POSIX-link test skipped; full v1.13 field build and live acceptance remain Pending. |
| Field rollout approval | Pending | Production ZIP verification is complete; all live installation, profile and Lesson3 acceptance checks remain Pending. Retain the documented fallback until evidence is reviewed. |

## Production v1.12 artifact

- Filename: `ARES_Q4_Offline_v0.94_amd64_v1.12.zip`.
- ZIP SHA-256: `fef897456108b70664fae280e4d3e4de354be23d3e0acbe4dc313dc1b458cd4a`.
- Size: 1,761,932,869 bytes.
- Builder commit: `973708935eacac62a210e7d065779090170733bf`, confirmed by
  the user; the ZIP manifest does not embed this Git identity.
- Manifest build time: `2026-10-30T13:16:47-07:00`.
- Profile: production (`ares.local`); Lesson3 v0.94; bundle revision v1.12.
- Corpus source commit: `e07c243da77ad4554a2f404ae7790ef6e9d3e1b0`;
  packaged manifest contains 95 plans / 806 lessons.
- Bundled approved APK SHA-256:
  `16e5eef24b56dde1db3fbd0e5be542c5853f329841ae056bc1dd7afb6bf773a8`.
- Windows copy:
  `C:/Users/MRKni/OneDrive/ARES Utilities/Offline Installer Releases/V1.1.2/ARES_Q4_Offline_v0.94_amd64_v1.12.zip`.
- User reports builder, independent verification and Windows copy verification
  passed. This update independently rechecked the Windows ZIP hash against its
  sidecar, ZIP CRC integrity, all 411 entries in internal checksum manifests,
  corpus manifest counts and the bundled APK hash; all passed.
- All live installation and field-acceptance checks remain **Pending**, including
  installed database counts. Packaged corpus counts do not establish import success.

## Known Issues / Lessons Learned

- TsavoTrust media belongs in the normalized external build source, not Git or
  Git LFS. Validate exact pinned paths/sizes/hashes before changing build outputs.
  Use UTF-8 explicitly when reading checksum filenames on Windows: one approved
  filename contains a curly apostrophe. Keep backup names hidden so portal scans
  do not discover duplicate cards. Root checksums must include nested manifests.
- Record manual component results separately from packaged acceptance. A successful
  manual TigerVNC test does not verify the packaged display, Tailscale transport or
  service lifecycle. Keep those gates Pending until their own evidence is reviewed.
- Android release builds may rename compiled XML (the approved APK uses
  `res/8G.xml`). Discover network-security policies by parsed structural strings
  beneath `res/`, retaining profile alias, DEX endpoint and application identity
  validation; never assume the source resource filename survives packaging.
- Software fixtures, debug APK builds and rendered guides do not establish live
  acceptance. Keep both profile columns Pending until actual target/client logs,
  package checksums and UI evidence support each result. See
  `offline-installer/docs/PROFILE_ACCEPTANCE.md` and
  `offline-installer/docs/LESSON3_V094_ACCEPTANCE.md`.
- This checkout had no root `STATUS.md`, `CLAUDE.md` or `WORKFLOW.md` when this
  update began. Use this file for continuity and the detailed profile/reconciliation
  documents for implementation evidence. The September deployment record in
  `docs/DEPLOYMENT_STATUS.md` is historical evidence, not acceptance of v1.12 profiles.
- Preserve existing untracked wrapper files and `-Destination`. Stage continuity
  paths explicitly; do not use broad staging for this update.

## Session Log

### 2026-10-30 - TsavoTrust integration for v1.13

- Retained Lesson3 v0.94 and bumped only the bundle revision to v1.13. Added a
  reviewed script-relative installer, pinned source manifest, standard-library
  validation and external-source packaging. No MP4s or Git LFS were added.
- Verified the read-only live key-map export SHA-256
  `f560bb4a0f70da2bee029a7c86a6630aefe18180b89ea2d0c619a237ab80eab1`.
  Its conventions and user-confirmed portal-link evidence support the TsavoTrust
  key and `www2/modules` link. Reconciliation preserves every existing byte and
  appends only `module:TsavoTrust,Tsavo Trust,`; no wholesale map replacement.
- Added validation before mutation, staged deployment on the destination
  filesystem, hidden backups, safe replacement of existing entries, exception/
  handled-signal rollback, installed-content checks and loopback portal/range
  verification. Missing, changed or conflicting inputs fail closed.
- Software suite:
  `python -B -m unittest test_tsavo_content test_tsavo_install test_profiles test_remote_support test_bundle_profiles test_offline_installer.OfflineInstallerSourceTests -v`
  with `PYTHONPATH=tests`: 46 tests run, 45 passed and one native POSIX-symlink
  test skipped. Windows transaction tests substitute only link creation/inspection;
  real copy, rename, backup and rollback operations execute. Three existing
  Linux/root corpus integration tests were not run on Windows. Ubuntu CI is
  configured for them and the native symlink test; no fresh CI result is claimed.
- Both fixture-profile scaffolds package successfully. Tests cover invalid input
  without replacing prior output, nested-manifest/root tampering, content errors,
  tracking conflicts, staging/publication/HTTP failure rollback and HTTP ranges.
  Shell syntax passed for all 18 scripts. A temporary normalized copy of the real
  payload passed all eight pins and six MP4 inspections, page correction and staged
  validation. The actual live-map comparison preserves the original bytes.
- Rehashed the verified v1.12 ZIP: its SHA-256 remains
  `fef897456108b70664fae280e4d3e4de354be23d3e0acbe4dc313dc1b458cd4a`.
  Its evidence files are unchanged. Remote-support code and checksum-bypass
  behavior were not changed; root nested-checksum coverage is the requested v1.13 fix.

Still open:

- Full production/test v1.13 build and independent artifact verification.
- Disposable Ubuntu native-link deployment, repeat/failure recovery and power-loss
  handling; actual portal/video playback, seeking and end-to-end tracking reports.
- All unperformed live installation, Lesson3, profile, packaged remote-support and
  rollout approval checks remain Pending. Stop after the dedicated Tsavo commit;
  no push or next implementation step is authorized by this checkpoint.

### 2026-10-30 - Remote-access field evidence

- Added [the v1.12 remote-access evidence record](offline-installer/docs/evidence/2026-10-30-v1.12-remote-access-field-test.md)
  and linked it from `offline-installer/docs/PROFILE_ACCEPTANCE.md` and this file.
- Recorded the user-reported manual TigerVNC component test as successful without
  claiming a new runtime test or packaged remote-support acceptance. No raw field
  transcript was supplied with the request. No authentication URLs, passwords,
  credentials or unredacted Tailscale IP addresses are included.

Still open:

- Packaged display `:1`, Tailscale-path SSH/VNC, reboot/autostart,
  disable/re-enable and activation failure cleanup remain Pending.
- All other live installation, profile, Lesson3 and rollout approval gates
  remain Pending.

### 2026-10-30 - Production v1.12 artifact verification record

- Recorded the successfully built production artifact, exact filename, ZIP hash,
  size, manifest build time, packaged corpus and APK identity, and Windows copy.
  Builder completion and independent verification were reported by the user;
  the Windows artifact and checks listed above were rechecked during this update.
- Recorded user-confirmed builder commit
  `973708935eacac62a210e7d065779090170733bf`; checked its identity in Git.
- Corrected the active artifact thread: a full production ZIP is now available
  and verified. Earlier no-full-ZIP statements describe the pre-build session.
  All live installation, field acceptance and rollout approval gates stay Pending.

Still open:

- Complete all live target, phone/client and Lesson3 UI/content acceptance gates.

### 2026-10-30 - APK policy resource discovery fix

- Replaced the literal network-security XML path with compiled-content discovery
  under `res/`. Unparseable resources are ignored; absent policies and any policy
  candidate with missing/wrong/mixed profile aliases fail closed. Both DEX endpoint
  checks and application identity validation remain enforced.
- Added regressions for `res/8G.xml` in both profiles, unrelated/malformed
  resources, missing/wrong/mixed policies, missing endpoints and wrong identity.
- Passed 27 tests with bundled Python 3.12 and Git Bash:
  `python -B -m unittest test_profiles test_remote_support test_bundle_profiles test_offline_installer.OfflineInstallerSourceTests -v`
  (`PYTHONPATH=tests`). The three Linux/root corpus integration tests were not run
  on Windows; they remain covered by the configured Ubuntu CI job, without a claim
  of a new CI result here.
- Confirmed the local release APK SHA-256 is
  `16e5eef24b56dde1db3fbd0e5be542c5853f329841ae056bc1dd7afb6bf773a8`;
  production verification passes. Existing production and test debug APKs also
  pass their respective verifier checks. No APK was rebuilt or modified.

Still open:

- All live profile acceptance and Lesson3 UI/content gates remain Pending.
- Complete field artifact and live target/client evidence before rollout approval.

### 2026-10-29 - Profile reconciliation continuity update

- Created this continuity record after reading the repository's current control
  and acceptance documents. The tracked working tree and index were initially
  clean; existing untracked files were left outside the update.
- Recorded the three consecutive implementation commits: `785825f` (canonical
  release metadata and profiles), `3dccba4` (optional remote activation and
  cleanup), and `608cb7e` (compiled profile/guide validation and acceptance records).
  Commit identities and scope were checked against live Git history.
- Marked all live production and permanent-test profile acceptance as Pending,
  including clean offline install, 95/806 corpus counts, client mDNS, Nginx/Lesson3
  URLs, phone discovery/collection, Tailscale enrollment, standard SSH, VNC tunnel
  and desktop, reboot/autostart, disable/re-enable, activation failure cleanup,
  and core success when optional support is declined or fails. Lesson3 discussion,
  administrator, content/regression and optional ZIP-import checks remain pending.
- Retained the earlier software evidence as historical evidence; no live tests,
  deployment, corpus import or rollout approval was performed by this update.

Still open:

- Produce and identify approved profile-matching field artifacts and checksums.
- Run and document every live acceptance check for both profiles on disposable
  Ubuntu targets with actual phones/clients, then review evidence before approval.
- Complete the Lesson3 v0.94 UI/content gates; retain fallback artifacts meanwhile.
