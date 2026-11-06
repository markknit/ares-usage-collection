# ARES Usage Collection Status

Last updated: 2026-11-06

## Current checkout

- Repository: `C:/Users/MRKni/Documents/ChatGPT/ares-usage-collection` (separate local clone).
- Branch: `simplify-offline-install`.
- Implementation baseline for this step: `728741b611d35ef9af1d69f7efcebd0bdda1bca7`.
- The C1-qualified tsavo3 checkout, normalized source and sealed evidence remain
  at the old baseline. Build this simplified source from a separate checkout;
  do not run the earlier C2 commands expecting the old behavior.
- Approved Lesson3 release: v0.94; current source bundle revision: v1.13.
- Production v1.13 built, independently verified and promoted on tsavo3; identity
  and operator-reported evidence below. Historical v1.12 retained unchanged.
- Production alias: `ares.local`; permanent test alias: `ares-test.local`.
- The corrected extracted test copy completed installation on tsavo3 on
  2026-11-01, according to the supplied operator transcript. The operator reports
  the three requested client feature checks passed, with the direct phone-page
  link correction below. Corrected release packaging, independent verification and Windows copy are
  complete. Clean installation of that ZIP and remaining acceptance are Pending.

## Active Threads

| Thread | Status | Evidence / next action |
|---|---|---|
| Simplified offline installation | Fresh installation reported working on November 5 except generic mDNS alias | Owner reports another fresh ARES installation worked, with tsavo3.local available but ares.local missing. No new raw installation log or detailed acceptance trace supplied; diagnose alias publication before closing the remaining field checks. |
| School hostname and generic mDNS alias | tsavo3 alias publication confirmed; other-server rename Pending | Supplied journal reports ares.local established on 192.168.12.113 and local resolution agrees. Owner confirms another ares.local server on the LAN. That older server lacks the new alias service; its failed commands made no changes. Avahi host-name=ares2 instructions supplied; resulting rename/client resolution not yet reported. |
| AnyDesk school identity | Manual recovery/reboot passed; latest rerun retained client and setup | Operator run `20261104_171914` reports existing personalization and desktop client retained. Earlier manual recovery/reboot connection passed. Explicit password/ID comparison and clean-image acceptance remain separate checks. |
| Phone installation-page link | Corrected source and ZIP complete | Installer, checks, guides and supplied admin link use `/app_install/index.html`; direct-page client acceptance on the fresh install remains Pending. |
| Offline ARES Sync manuals | Packaged and copied to Windows | Technician/teacher guides, approved protected manual and two-page component/process overview are in the corrected ZIP and Windows Documents folder. All five copied PDFs match their ZIP entries. |
| Editable technician installation guide | Updated and visually reviewed on November 6 | New `output/docx/ARES_Technician_Installation_Guide_20261106.docx` includes offline LAN support. Four pages, 69 editable source content blocks, all final pages reviewed. November 5 copy retained; owner's own additions have not been supplied. |
| Owner-approved admin pages and manual | Published and included in corrected ZIP | Supplied pages/manual remain unchanged. The teacher-app stage deploys the three together, backs up old files and preserves metadata/folder protection. No additional manual functional tests were run. |
| Internet Lockdown v1.4.2 | Disconnected-safe command installation packaged; live check Pending | Original release/rule bytes retained. New wrapper installs commands without an adapter/terminal and asks for the actual student LAN at first use; restore works without a LAN selection. Active/boot lockdown preserved. |
| Corrected v1.13 ZIP and technician overview | November 4 r2 verified and on Windows; fresh install Pending | [Release evidence](offline-installer/docs/evidence/2026-11-04-v1.13-simple-remote-release.md): distinct `20261104-r2.zip`, 341 files, hash `fb10499c...`, 120 Ubuntu tests. Reviewed two-page overview/four-page technician guide and all copied documents match the ZIP. Earlier artifacts unchanged. |
| tsavo3 pre-reload preservation | Known changes/build inputs verified off-server | Private configuration/web/database backup passed all 29 checks on host and Windows; original/normalized sources and sealed evidence archive also copied and hash-verified. Owner supplies Clonezilla base/library. Temporary SSH key removed. Owner subsequently reloaded the base and reported the standalone installation; backup restoration itself has not been tested. |
| Simplified-r3 production artifact | Historical payload retained; corrected ZIP now available | Original `1f0993a8...` artifact remains unchanged and retained on Windows. Use the corrected `d3dc1c30...` ZIP for the next installation test; see the new release evidence. |
| Explicit root-checksum recovery | Retired by project-owner direction | Historical fixture evidence retained; the simplified source removes the alternate installer and its receipt/controller code. Replace an incomplete ZIP rather than bypassing its check. |
| v1.13 native Linux fixture validation | Passed for tested commit; field gates Pending | Ubuntu 24.04.2 LTS x86_64, commit `350690f`: 24 shell checks, 87 unprivileged Python tests, three root corpus-status tests, portal/PHP fixtures and native POSIX symlinks passed; repository clean. External archive SHA-256 and four log hashes verified. See [native fixture evidence](offline-installer/docs/evidence/2026-10-31-v1.13-linux-fixture-validation.md). |
| Complete recovery-through-PTY CI regression | Retired with recovery feature | Replaced by normal-workflow rejection and optional-support failure tests. Historical native evidence is unchanged. |
| Canonical release metadata and sealed profiles | Implemented; live acceptance pending | `785825f` records release configuration, profile rendering and Android endpoint changes. Verified with `git show --stat 785825f`. |
| Optional SSH / TigerVNC support | Browser SSH/direct saved-viewer passed manually; automated setup packaged in r2 | Reauthentication addressed stale registration. The owner connected directly with RealVNC after configuring Serve and connecting Windows Tailscale. r2 automates browser SSH/operator and persistent private forwarding; 120 native tests passed. Its own activation/clean-image and reboot/disable/re-enable remain Pending. |
| Offline LAN/headless desktop | November 6 implementation, 124 Ubuntu tests and independent packaging passed | Source aa0011c, full dated ZIP 73efc019... (341 files), support update 4862a66c... (8 files), both in `Downloads/ARES_v1.13_Release_20261106`. LAN-first password-required port 5901 and `--lan-only` retain Tailscale state/forwarding. [Release evidence](offline-installer/docs/evidence/2026-11-06-v1.13-lan-desktop.md). Actual disconnected-LAN/headless/reboot and retained Tailscale viewer checks remain Pending. |
| Manual TigerVNC component field test | Successful - user-reported; packaged acceptance Pending | See [2026-10-30 remote-access evidence](offline-installer/docs/evidence/2026-10-30-v1.12-remote-access-field-test.md). Packaged display `:1`, Tailscale-path SSH/VNC, reboot/autostart, disable/re-enable and failure cleanup remain Pending. |
| Compiled profile and guide validation | Software evidence recorded; live acceptance pending | `608cb7e` records compiled profile checks, guide rendering, alias audit, CI configuration and acceptance records. Verified with `git show --stat 608cb7e`; earlier software-test results are recorded in `offline-installer/docs/PROFILE_ACCEPTANCE.md`, not rerun by this documentation update. |
| Obfuscated APK policy resources | Fixed and locally validated; live acceptance pending | `verify_apk()` discovers compiled policies beneath `res/` using structural strings, ignores unparseable resources, and rejects missing/wrong/mixed policies. 27 local tests passed on 2026-10-30; approved production APK and both debug profiles pass verification. |
| Production profile live acceptance | Earlier operator feature checks passed; corrected-ZIP clean acceptance Pending | Prior operator results remain recorded. The new ZIP is verified and copied to Windows, but clean installation, remaining tracking/support/reboot and deeper feature checks need their own evidence. |
| Permanent test profile live acceptance | Pending - all checks | Every permanent-test column entry in `offline-installer/docs/PROFILE_ACCEPTANCE.md` remains Pending. Includes actual discovery/collection and the Lesson3 UI/content gates. |
| Production v1.12 artifact | Built and independently verified; live acceptance Pending | `ARES_Q4_Offline_v0.94_amd64_v1.12.zip`, built from `973708935eacac62a210e7d065779090170733bf`; identity and verification evidence below. |
| TsavoTrust v1.13 integration | Host verification and requested browser/video check passed by operator report; tracking/recovery Pending | Run `20261101_111100` passed content/link/mapping and HTTP checks. Operator reports all three requested feature checks passed, including Tsavo videos. Report attribution, repeat/failure recovery and remaining acceptance are Pending. |
| Field rollout approval | Pending clean installation and remaining live acceptance | Corrected artifact includes storage-alias/direct-page fixes, approved admin content and Internet Lockdown v1.4.2 and passed independent verification. No field acceptance inferred from packaging. |

## Latest software-verified candidate (November 6 LAN desktop)

- Source: `aa0011ca320a7b014d1e174bae96039abd6ddb3f`.
- ZIP: `ARES_Q4_Offline_v0.94_amd64_v1.13_20261106.zip`.
- SHA-256: `73efc0192fb0fc732139d5720e16cd9dfb6c59e61b4d7dc9d3464f14a7fa7457`.
- Windows folder: `C:/Users/MRKni/Downloads/ARES_v1.13_Release_20261106`.
- Full installer: 341 independently verified ZIP files. Support-only update:
  eight verified files; no content/AnyDesk rerun needed for an installed server.
- 121 Windows tests run, 119 passed and two native-only tests skipped. Native
  Ubuntu CI run 42187158472 passed all 124 tests for the exact packaging source,
  including the Linux/root cases unavailable on Windows.
- Two PDF guides and a new editable Word guide reviewed; all six packaged PDF
  page images match the reviewed pages. Documents and instructions copied off-server.
- [Release identity and limits](offline-installer/docs/evidence/2026-11-06-v1.13-lan-desktop.md).
- No installer/update ran during packaging. Live offline/headless/reboot and
  remaining acceptance stay Pending. Earlier artifacts remain unchanged.

## Previous software-verified candidate (November 4 revision 2)

- Source: `656cbc24a432588f3fd59940bfc1447bc49e0fdd`.
- ZIP: `ARES_Q4_Offline_v0.94_amd64_v1.13_20261104-r2.zip`.
- SHA-256: `fb10499cadc1abd1320347d39b20a7643823b8ec4b0241cec425e9e0fbe9bf8a`.
- Windows folder: `C:/Users/MRKni/Downloads/ARES_v1.13_Release_20261104_r2`.
- 341 ZIP files independently verified; 120 Ubuntu tests passed.
- [Release identity, reviewed handouts and acceptance limits](offline-installer/docs/evidence/2026-11-04-v1.13-simple-remote-release.md).
- Manual browser SSH/direct RealVNC and AnyDesk recovery/reboot are reported
  successful. This new artifact's own clean installation/activation and remaining
  field checks stay Pending. It was built without running an installer.

## Previous software-verified candidate (November 4)

- Source: `29c3a1e11b48299b2021199a016ac0e17d213047`.
- SHA-256: `bc1b1f8e1a79d38f6faa97527b2869e857aea2f74074f085e6be0c79b9d7edaa`.
- Windows folder: `C:/Users/MRKni/Downloads/ARES_v1.13_Release_20261104`.
- 341 ZIP files independently verified; 114 Ubuntu tests passed.
- [Candidate identity and limits](offline-installer/docs/evidence/2026-11-04-v1.13-remote-support-candidate.md).
- **Manual AnyDesk recovery and a connection after reboot passed by operator
  report**, following ownership repair and a fresh user profile. Explicit
  unattended authentication/ID comparison, corrected-installer rerun and clean
  installation of this candidate remain Pending; no field rollout is approved.

## Current production v1.13 artifact (November 3)

- Source: `96281fc50741e539f1f3131c9dd4265abcb4a2bc`.
- SHA-256: `195a140f9acea56b7237b84e35a6853b3cb1a0939224db0060e456178a8372fe`.
- Independent verification: 340 files; Windows hash confirmed.
- Windows folder: `C:/Users/MRKni/Downloads/ARES_v1.13_Release_20261103`.
- [Full and small update evidence](offline-installer/docs/evidence/2026-11-03-school-setup-update.md).
- [Small offline update for an already-installed server](offline-installer/updates/README.md).
- Ubuntu CI: 104 tests passed. New live checks remain **Pending**.
- November 2 `d3dc1c30...` ZIP and preservation backups remain unchanged.
  Its [historical release evidence](offline-installer/docs/evidence/2026-11-02-v1.13-corrected-release.md)
  still records the pre-reload copies and their limits.

## Original production v1.13 artifact (retained payload baseline)

- Filename: `ARES_Q4_Offline_v0.94_amd64_v1.13.zip`.
- ZIP SHA-256:
  `1f0993a806b41aa7024e0f4af7e634e7186f9d08983669a88d91c45a93b692c9`.
- Location:
  `/mnt/sda3/home/ares/Downloads/ARES_Q4_Update_offline_v1.13/ARES_Q4_Offline_v0.94_amd64_v1.13.zip`.
- Final qualification source: `487dea05b7bf5a8ba1d2863b8e37884adb537612`;
  assembly/repackaging identities are recorded separately in the
  [artifact evidence](offline-installer/docs/evidence/2026-10-31-v1.13-production-artifact.md).
- Operator-supplied tsavo3 output confirms all independent checks passed:
  313 ZIP files, 133 approved inherited files, one newline-normalized comparison,
  unchanged final ZIP bytes and successful promotion. Not rechecked locally by
  the build-record documentation update. No installer ran during the build;
  later corrected test-copy installation is recorded separately above.

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

- On-site headless support must not depend on Tailscale enrollment or Internet.
  Activate password-required LAN VNC before optional enrollment, preserve it when
  enrollment is deferred, and offer an explicit LAN-only command. Retain the
  loopback endpoint for existing private Tailscale forwarding. Test both the
  disconnected LAN path and remote path; a failed local-IP connection to the old
  loopback-only configuration did not establish that the VNC service was stopped.
- Published technician PDFs have three tracked copies: `output/pdf/`,
  `offline-installer/docs/pdf/` and the embedded rollout's `guides/`. After
  regeneration, synchronize all three and refresh the embedded SHA256SUMS.
  Run the source-guide/manifest checks before publishing; updating only the
  installer-docs copy caused a CI mismatch during the r2 documentation sync.
- Browser Tailscale SSH has its own ephemeral tailnet connection. It does not
  connect the Windows desktop apps to the tailnet. For saved VNC/PowerShell
  access, the support computer's Tailscale app must be connected separately.
  Keep this explicit in the technician workflow; the owner confirmed direct
  RealVNC worked after connecting the Windows app. Use private persistent Serve
  forwarding for routine VNC rather than requiring a manual SSH tunnel.
- Preserve the supplied Internet Lockdown release and its own checksum manifest
  unchanged, excluding it from profile substitution. Its handoff STATUS is a
  historical upstream document; repository-root STATUS and the integration guide
  record later import/deployment decisions. Installation prepares tools without
  activating rules or choosing boot persistence. Do not restart/replace optional
  support services while active or boot-enabled lockdown may depend on their
  service-cgroup identity.
- An upstream error message recommending `apt-get install nftables` is not an
  executed package installation. The shared offline audit exempts only that
  exact line at the sealed versioned script path; actual install/download
  commands and the same text in other script paths remain rejected.
- A directory URL returning HTTP 200 may be the ARES file manager, not the
  requested installation page. Use `/app_install/index.html` explicitly and
  require the expected page title in the installed HTTP check. Do not infer
  correct page delivery from a successful status alone.
- Declining optional remote activation does not mean preparation left older
  support services unchanged: the successful tsavo3 transcript explicitly shows
  `x11vnc.service` being disabled. Record that change and verify existing VNC
  access separately; core installation success does not establish support access
  or firewall persistence after reboot.
- ARES can expose its mounted disk through the `/mnt/sda3` symlink. Resolve that
  configured anchor before Tsavo destination checks, while rejecting symlinked
  parents below it and preventing alternate test roots from escaping. The original
  v1.13 ZIP remains byte-verified but has this known deployment defect; build
  verification alone did not establish compatibility with the live disk layout.
- Docker saved-image TARs can use internal links for shared layers. Resolve them
  within archive metadata rather than rejecting every link; retain regular-file,
  image identity and platform checks. Real archive metadata and regression
  fixtures cover this layout.
- Compare inherited text using the same newline convention as its sealed approval
  record; preserve and record the raw ZIP bytes. Read the final ZIP directly,
  report all discrepancies together and reuse a verified unchanged ZIP during
  resume instead of repackaging it for a build-side comparison correction.
- The project owner approved a simpler offline deployment model on 2026-10-31:
  keep automatic corruption checks and functional checks, remove repeated manual
  qualification and the bypass path, and prevent optional remote prerequisites
  from blocking core installation. Earlier byte-identical-installer/recovery
  instructions below and in historical session logs describe the superseded design.
- Detailed component checks run on a fresh ZIP extraction automatically at build
  completion. Field preflight performs one complete-package inventory/hash check.
  Standalone component utilities retain their own local checks; corpus status
  checks no longer rehash the same files before and after import.
- The retired checksum-bypass feature's native PTY results are historical, with
  complete orchestration covered only by an inline operator fixture. Preserve
  that evidence, but do not resume its old CI task or apply its bypass/receipt
  instructions to the simplified installer. Replace an incomplete package instead.
- Remote command-line readiness and desktop readiness are separate outcomes.
  After Tailscale/SSH succeed, a VNC failure must diagnose and stop only the owned
  VNC unit, return partial failure and retain the working command-line path. Send
  enrollment output to the controlling terminal rather than original stdout:
  original stdout may already be a parent installer's log pipe. Preserve both
  SSH service/socket baselines and do not enable a service behind an active socket.
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

### 2026-11-06 - Offline LAN desktop alongside Tailscale

- Owner authorized direct LAN VNC for school visits without Internet, including
  headless servers. Added password-required network listening while retaining the
  loopback endpoint used by Tailscale Serve and the existing VNC password.
- LAN SSH and VNC start before optional Tailscale enrollment. Deferral keeps them
  running. `sudo ares-enable-remote-access --lan-only` skips hostname changes and
  all Tailscale operations. Existing service/identity/forwarding are retained.
- Added a separately packaged support-only updater for installed v1.13 servers;
  it installs canonical controls, backs up previous controls and runs LAN-only
  activation. No Lesson3 import, AnyDesk reset or Internet download is involved.
- Updated technician source guides, acceptance procedure, two reviewed PDFs and
  a new four-page editable Word guide. Synchronized the three technician PDF
  copies and refreshed the embedded rollout checksum. November 5 Word copy and
  previous full installers remain unchanged.
- Windows regression passed: 121 tests run, 119 passed and two native-only tests
  skipped; the three Linux/root corpus tests are reserved for Ubuntu CI. All
  installer shell syntax checks passed. Full packaging independently verified 341
  ZIP files, retaining 267 base files and classifying 74 updated/new entries.
  The eight-file support-only ZIP was independently extracted and verified too.
  Both are in a new November 6 Windows Downloads folder. Source aa0011c is pushed;
  native Ubuntu CI run 42187158472 passed all 124 tests and shell checks. Exact
  hashes/verification are in the release evidence. Packaged PDF page images match
  the reviewed pages; all published copies match the delivered PDF bytes.
- Confirmed from supplied logs that tsavo3 publishes/resolves ares.local. Another
  server using the same name explains the reported coexistence concern; the
  older server lacks the new alias service. Supplied an Avahi-only rename
  procedure; no resulting client test has been reported yet.

Still open:

- Actual LAN VNC with Internet disconnected, headless/reboot access, and retained
  Tailscale viewer access. Remaining field acceptance/rollout stay Pending.

### 2026-11-05 - Fresh-install report and editable technician guide

- Owner reports the fresh installation worked except that only tsavo3.local,
  rather than both it and ares.local, was available. Requested read-only alias
  service status/journal, selected address and resolution output, plus whether
  another ARES server is on the LAN. Root cause and recovery remain Pending.
  No live-host network or installer source change was made on this evidence.
- Created an editable Word version of the published r2 technician guide for the
  owner's additions. All 68 source content blocks are retained as editable text;
  the document uses native Word heading/list structures and is not protected.
- Rendered with native Microsoft Word conversion through the packaged renderer's
  PNG pipeline because LibreOffice is not bundled on this Windows host. Reviewed
  all four final pages, including restarted lists and clear section boundaries.
- Saved the document in `output/docx/` and Windows Downloads; copied bytes match
  the reviewed file. Existing PDFs and the verified r2 ZIP remain unchanged.

Still open:

- Review the server's alias diagnostics, correct the confirmed mDNS cause and
  verify ares.local from another LAN device alongside the hostname.
- Incorporate the owner's Word edits when supplied; remaining unperformed field
  checks and rollout acceptance remain Pending.

### 2026-11-04 - Verified r2 Windows package and updated handouts

- Built from canonical committed source `656cbc2`. Exact-source Ubuntu CI passed
  all 120 tests and shell syntax checks (run `41955491774`, job `127009289837`).
- Fresh independent extraction verified all 341 ZIP files; 267 untouched base
  files were retained and 74 updated/new files recorded. Final ZIP hash is
  `fb10499cadc1abd1320347d39b20a7643823b8ec4b0241cec425e9e0fbe9bf8a`.
- Saved a distinct `20261104-r2.zip` in the new Windows r2 directory. Five PDFs
  and three supplementary Markdown documents match their ZIP members. Visually
  reviewed every page of the two-page overview and four-page technician guide.
- No installer, Docker operation or download ran during packaging. Older ZIPs,
  original media/inputs, private backups and v1.12 were retained unchanged.
- Manual support results and the same-school AnyDesk retention policy are
  recorded in the [r2 evidence](offline-installer/docs/evidence/2026-11-04-v1.13-simple-remote-release.md).
- The documentation publication check caught the older duplicate technician
  PDFs. Synchronized all three tracked copies and refreshed the embedded
  checksum; all 11 source checks then passed locally. This aligns repository
  documentation with the already verified ZIP and does not change ZIP bytes.

Still open:

- Fresh r2 installation/activation, direct-route reboot/disable/re-enable,
  explicit identity/password comparisons and remaining field acceptance.

### 2026-11-04 - Simplify routine support login after the full rerun

- Latest operator run `20261104_171914` passed package/core checks, retained healthy
  Lesson3/corpus and existing AnyDesk personalization/client, and preserved active
  Tailscale/TigerVNC during preparation. Nginx reported duplicate MIME warnings
  but its configuration check passed; no unrelated Nginx change was made.
- Tailscale 1.104.1 reported Running but Self.Online false and repeated coordination
  `404: node not found`, while UDP/IPv4/IPv6 relay tests succeeded. A fresh sign-in
  was requested through independent access. The owner subsequently confirmed
  browser SSH after enabling Tailscale SSH/operator manually. No enrollment URL,
  password or real tailnet address is stored in this record.
- TigerVNC binaries and the enabled :1 unit were present, listening on loopback
  port 5901. The owner confirmed a working VNC desktop through the LAN SSH tunnel
  but rejected that sequence as too complicated for routine technician use.
- Source follow-up enables Tailscale SSH and operator ares automatically. A
  persistent private Serve TCP/5901 forward reaches the existing loopback VNC
  listener. Existing matching routes are reused; unrelated routes, conflicting
  handlers and public Funnel configurations are not overwritten. A forwarding
  failure leaves working SSH and local TigerVNC running.
- Activation prints saved-viewer instructions and actual coordination health;
  normal retries still do not force reauthentication. Updated technician and
  acceptance Markdown records the simpler workflow. The earlier RunSSH=false
  default is superseded by the owner's requested browser SSH workflow.
- Clarified school identity handling: first setup replaces the cloned AnyDesk
  ID, while completed same-school reinstalls preserve it. The reusable base must
  predate school personalization; otherwise a copied completion record can make
  a clone appear configured. Deliberate reassignment remains an explicit reset.
- Forty-one local remote-support/source tests passed on Windows/Git Bash.
  The owner subsequently confirmed direct RealVNC access after reconnecting the
  Windows Tailscale app. Browser SSH alone had not connected the desktop client.
  Updated activation, reboot/disable/re-enable, regenerated release PDFs and a
  new full ZIP remain Pending. Native Ubuntu CI passed all 120 tests for
  `4e8e748e986f6b3c1dc67303483e5f7eac214cdf`, plus shell syntax checks:
  https://github.com/markknit/ares-usage-collection/actions/runs/41955233294
  (job `127008447489`). The existing
  November 4 ZIP is unchanged and contains the older activation behavior.

### 2026-11-04 - Manual AnyDesk profile recovery restored a connection

- The SSH desktop launch test found X11 display `:0` but exited with SIGABRT.
  The available Apport report records an earlier 10:26 `--backend` crash and
  contains no usable function names; it does not establish the current cause.
- The first fresh-profile attempt failed at the profile move with Permission
  denied, before launch. After user-profile ownership/permission repair, the
  operator's successful rerun retained the previous profile in
  `/home/ares/anydesk-profile-test.f9wZUSgP/previous-profile` and launched the
  client through a temporary user service. The operator confirmed a remote
  connection and reported that the unattended password was lost.
- This is manual recovery evidence, not a clean installation of the November 4
  candidate. Password restoration, actual unattended authentication, recording
  the current ID and reboot/autostart/reconnection remain Pending. Do not clear
  a working profile automatically on ordinary installer reruns.
- No runtime code, release ZIP or live-host setting was changed by the agent
  while recording this operator evidence.
- The operator subsequently confirmed AnyDesk still works after restart. This
  establishes a post-reboot connection, not corrected-installer rerun behavior
  or a separately documented password/ID comparison.
- Rechecked the November 4 ZIP's master installer, AnyDesk preparation/setup and
  desktop helper against committed source: all four match. Fourteen existing
  school-setup/desktop tests passed on Windows with Git Bash after allowing
  normal temporary-file access; the restricted run failed on fixture directory
  permissions. These are simulated lifecycle tests, not a real AnyDesk rerun.

### 2026-11-04 - SSH rerun and remote-support recovery

- Owner supplied the complete `20261104_102223` install transcript. Core passed:
  mDNS service installed, healthy existing Lesson3 retained, corpus status already
  installed, tracking/admin/APK/Tsavo and installed-service checks passed.
- AnyDesk reset/password/new numeric ID completed, but unattended desktop access
  returned `desk_rt_ipc_error`. Root service was online; the graphical client was
  absent. A relaunch found the X11 session but aborted. The user profile was
  root-owned; ownership repair and another launch still did not restore access.
  A normal reboot was tried; the owner reports the same error. Trace/version/crash
  report details were requested. Do not infer live
  desktop recovery from a new ID, successful password CLI or service readiness.
- Optional preparation disabled x11vnc and left Tailscale/TigerVNC inactive.
  Activation received an empty/unusable school name and stopped before enabling
  Tailscale. No lockdown table was active; restore reported no table present.
- Follow-up source keeps the current hostname on Enter, reprompts invalid input
  without a traceback and preserves existing service states/x11vnc during remote
  preparation. AnyDesk root CLI omits desktop variables and uses root's HOME;
  the new desktop helper repairs user-folder ownership, locates the actual X11
  environment and launches as ares. Client abort/no desktop returns Pending.
- Local fixtures verify input handling, state preservation, ownership and client
  startup/failure handling without touching a server. Native CI passed 114 tests;
  full candidate passed independent 341-file verification. [Candidate evidence](offline-installer/docs/evidence/2026-11-04-v1.13-remote-support-candidate.md)
  records the Windows identity and unresolved live crash. No new server SSH access was established;
  recovery commands were run by the owner in the existing SSH session.

### 2026-11-03 - Standalone-install follow-up: local names, lockdown and AnyDesk

- Owner reports the offline install on a freshly loaded server ran well with two
  exceptions: no generic ares.local alias and lockdown setup refused an absent
  active adapter. Added the requested AnyDesk clone personalization step.
- Restart check: expected branch `simplify-offline-install`, clean initial HEAD
  `8bd06d7` matched GitHub; no CLAUDE/WORKFLOW/active HANDOFF controls in this
  checkout. Preserved the existing profile/acceptance boundaries and old artifacts.
- Extracted the mDNS publisher/setup into reviewed helpers. Avahi preserves the
  machine hostname; Nginx includes it alongside the generic profile alias.
  Publisher waits offline, supports link-local IPv4 and retries exited children.
- Lockdown installation now installs commands without a connected adapter or
  terminal. First activation selects the real student LAN; restore bypasses LAN
  selection. Original v1.4.2 imported project/rules remain unchanged. Existing
  active/boot lockdown still defers upgrades and optional service restarts.
- AnyDesk helper archives both system.conf/service.conf and the desktop user's
  configuration after local RESET confirmation, configures the hidden unattended
  password through the supported CLI, and displays/saves a different numeric ID.
  Pending ID/password setup can be retried without resetting again. No password
  is hardcoded or committed. Existing lockdown prevents service reset.
- Builder and independent verifier include every new helper. Added a small
  offline update packager for the already installed server, without reinstalling
  content/database. Repack ZIP Unix file modes are explicit on Windows too.
- Focused portable fixtures passed 44 tests before final documentation refresh;
  all installer shell scripts parsed. Updated two technician PDFs and visually
  reviewed every page. Native Ubuntu CI then passed all 104 tests. Full ZIP
  independently passed 340-file verification; small offline update passed 29-file
  extraction/inventory checks. [Final identities and limits](offline-installer/docs/evidence/2026-11-03-school-setup-update.md)
  are recorded, with Windows copies and the small update retained in Git.
- No actual server commands, AnyDesk resets or firewall changes performed here.

### 2026-11-02 - Corrected ZIP and Windows preservation handoff completed

- Repack source `3053d50` passed all 98 Ubuntu tests. Fresh r3 output passed
  full independent verification of 332 ZIP files and was promoted with hash
  `d3dc1c301290a398a30478cbd8a2ee804a31b78a8bdffd7a88aaf00f07b4edf2`.
  Preserved 267 base files; updated/added 65. Failed earlier candidates retained.
- Windows final ZIP hash and all five PDF copies match. Linux-generated overview
  has two visually reviewed pages. Added Windows START_HERE instructions and
  copy-verification record; old ZIP retained under a clearly different name.
- Private configuration/web/DB backup completed; all 29 checks passed both on
  host and Windows. Original/normalized source plus sealed evidence archive also
  passed its Windows checksum. Backups remain outside GitHub/technician docs.
- Removed only the temporary SSH authorized-key entry and deleted its local key
  files. No installer, reload, service restart, firewall activation or Docker
  operation ran during this packaging/preservation work. v1.12 unchanged.
- [Release evidence](offline-installer/docs/evidence/2026-11-02-v1.13-corrected-release.md)
  records exact paths, identities and preservation limits. Owner-controlled
  Clonezilla restore, clean installation and remaining live acceptance are next.

### 2026-11-02 - Corrected release packaging and pre-reload handoff

- Owner authorized building the corrected ZIP, copying it to Windows and adding
  a technician component/process overview, then clarified that the upcoming test
  restores the whole disk from an existing Clonezilla baseline of this system
  without offline-installer additions. The live layout has Ubuntu on sda2 and
  the data/build area on sda3, on the same disk. The Clonezilla image's unchanged
  library coverage is owner-reported, not independently verified here.
- Established authorized temporary-key SSH access after hostname resolution and
  keyless authentication were unavailable. Build/file-copy operations run as
  ares. The owner ran the reviewed private preservation helper with sudo in the
  existing terminal; no password was collected in chat. No reload, firewall
  change or service restart was performed. Remove the temporary key when done.
- Copied the original production ZIP to Windows and confirmed its recorded
  `1f0993a8...` SHA-256. Prepared separate preservation of original/normalized
  sources and sealed evidence. A private configuration/changed-page archive and
  current Lesson3 dump completed on-host and passed its checksums; off-server
  copying remains in progress at this source commit. Private data stays outside
  the repository and must not be published with technician documentation.
- Added a pinned-base repackage tool: fresh output only, current reviewed scripts
  and approved payloads, regenerated guides/checksums, unchanged-base-file
  comparison and full independent ZIP verification before promotion. It does
  not run an installer, pull/download or change Docker. Added three passing
  disposable workflow tests, including wrong-base/existing-output rejection and
  failed-verification retention without promotion. Backup helper syntax checked.
- The first actual candidate stopped at independent verification because the
  updated Tsavo helper still had its old component checksum list. It was not
  promoted and remains marked incomplete. Corrected the repack tool to reseal
  that component and strengthened the existing workflow check for nested Tsavo
  and teacher-app checksums before retrying in a fresh output folder.
- The next candidate passed component checks but stopped at the raw Tsavo
  source-pin reference. Comparison with the original qualified checkout proved
  the JSON content was identical: the Windows Git archive had exported CRLF
  instead of LF. No pin values/media changed. Source exports now explicitly
  disable autocrlf and pinned JSON uses LF attributes; the repack tool rejects
  this mismatch before staging. Failed candidates remain unpromoted.
- Added a two-page technician overview and a pre-reload preservation guide.
  Generated and visually reviewed both overview pages; distinguish server school
  ID from the phone's separate one-time enrollment key. The normal full builder
  and corrected repack both include the documents and generated overview PDF.

Still open:

- Complete actual corrected-ZIP verification and the Windows copy/checksum.
- Confirm private backup/build-input archives are complete and verified off-server.
- Remove temporary SSH access, record final artifact identity, then hand back for
  the owner's clean Clonezilla/offline-install test. No reload is authorized here.

### 2026-11-02 - Integrate supplied Internet Lockdown v1.4.2 project

- Restart verification found the expected clean `simplify-offline-install`
  checkout at `45cfd18`, matching GitHub after fetch. Main has eight unmerged
  commits; no merge, base change or new branch was requested or performed.
- Read the supplied project STATUS, both operating-PDF pages, README, release
  notes and installer/scripts as source material. Imported all ten handoff files
  into `offline-installer/internet-lockdown/`, preserving exact ZIP bytes and
  the original eight-file release manifest. The imported upstream STATUS still
  describes its earlier no-destination/no-push handoff; this record supersedes
  those historical integration-status statements without altering that source.
- Builder packages the project under the existing generated `remote-access/`
  tree, with independent exact-byte/source and upstream-manifest verification.
  Profile rendering skips this sealed project, retaining its original production
  examples and PDF. No uploaded firewall code or hashes were changed.
- Added a preparation stage after successful core/optional-remote setup. It keeps
  the source/docs under `/opt/ares/internet-lockdown/` and invokes only the
  supplied `install.sh --no-boot` when suitable. LAN discovery/selection remains
  upstream behavior. Active or boot-enabled lockdown, missing dependencies or
  noninteractive input defer setup; existing runtime rules/configuration remain
  untouched. Optional failures keep the completed core installation successful.
- Optional remote preparation now defers while lockdown is active/boot-enabled,
  preserving existing Tailscale/remote services and their cgroup exceptions.
  The supplied project documents known AnyDesk recovery, mesh, IPv6 and reboot
  limitations; no live acceptance is inferred from the import or mock checks.
- Fixed the offline audit false positive on the upstream dependency-error echo
  using one exact path/message exception shared by builder and ZIP verifier;
  real network installation commands are still rejected. Added integration
  tests with fake firewall/service/upstream commands, covering no-boot invocation,
  active/boot deferral, noninteractive input, upstream failure and core-success
  preservation. All 23 focused Windows tests passed, including both-profile
  scaffold/fresh-ZIP fixtures; all nine imported/changed shell scripts parsed.
- No real installer, firewall operation, service change, release build or Docker
  operation ran. Existing admin-content approvals and v1.12 remain unchanged.
- Published source `5a1f5bef89ece7c77f3184a770c81a6cbfa5059a` on
  `simplify-offline-install`; remote commit identity and clean Windows checkout
  verified. Native Ubuntu offline-installer CI passed all 94 tests and shell
  syntax checks: https://github.com/markknit/ares-usage-collection/actions/runs/41495393636.
  The profile-renderer change also triggered the separate Android workflow;
  that build does not replace the approved production APK or v1.12 artifact.

Still open:

- Corrected field ZIP/release verification with all accumulated additions.
- Live project acceptance and remaining support/reboot/tracking work.

### 2026-11-01 - Group owner-approved admin content into the installer

- The owner supplied and explicitly approved the already tested admin page,
  Admin_tools module entry and renamed ARES Sync user guide for one content
  deployment unit. Imported the files without editing their HTML/PDF bytes.
  Marked the content files against Git text conversion to preserve exact bytes.
- Interpreted the supplied `/mt/sda3` manual path as `/mnt/sda3`, matching the
  two other destinations and the existing storage path. The final targets are
  `/mnt/sda3/var/www/admin/admin.html`,
  `/mnt/sda3/var/www/modules/Admin_tools/index.htmlf` and
  `/mnt/sda3/var/www/admin/ARES_Sync_User_Guide.pdf`.
- Builder packages the three files and grouped deployment helper inside the
  existing generated teacher-app component. Normal step 5 calls the helper;
  no extra technician command is needed. It prechecks the three inputs, backs
  up prior files together and replaces only the named content. Existing file
  ownership/modes and destination-directory/authentication settings are retained.
- Kept the supplied manual separate from regenerated teacher/technician guides.
  Existing root/component checksums cover the new files, and independent ZIP
  verification compares the approved content byte-for-byte. Updated existing
  packaging fixture inputs for the added files; no new tests were added and no
  tests were run manually for this content update. Configured GitHub CI may run
  automatically when the branch is published.
  Only file-copy integrity and installer wiring were reviewed, honoring the
  owner's explicit direction against additional functional testing.

Still open:

- Publication resolved: the owner explicitly authorized pushing the supplied
  files to public GitHub; integration `3ead31a1e7f056e0816b6d7bee9ad3d79093634e`
  was pushed and the remote branch identity verified. Original page whitespace
  is deliberately retained to preserve the supplied files exactly.

Still open after publication:

- Package and independently verify the corrected field ZIP with these content
  changes and the earlier storage-alias/direct-page fixes. No server deployment
  or release rebuild was performed by this source update.
- Remaining support/reboot/tracking and field acceptance work remains separate.

### 2026-11-01 - Refreshed offline installation and user manuals

- Located general Internet-download manuals and the separate local-school-server
  source guides. Generated fresh offline PDFs under `output/pdf/offline/` from
  the current offline Markdown, including `/app_install/index.html`. Preserved
  existing general PDFs, bundled historical PDF copies and v1.12 artifacts.
- Updated the shared renderer footer revision to 2026-11-01. Teacher manual:
  two pages; technician manual: three pages. Extracted text confirms the direct
  installation link and revision on every page; rendered and visually inspected
  all five pages. No software regression tests were needed for this PDF/footer
  documentation step.
- Linked the refreshed manuals from README and documented copying both PDFs to
  the existing server downloads directory. The teacher PDF covers installation
  and normal use. No server command, admin-menu edit, live copy verification or
  release rebuild was performed; those actions remain separate.

Still open:

- Transfer PDFs, run the supplied copy command on Ubuntu and add desired menu links.
- Remaining corrected ZIP, support/reboot/tracking and field acceptance work above.

### 2026-11-01 - Client feature report and direct phone-page link

- Operator reports all three requested ARES feature checks passed: portal/Tsavo,
  Lesson3 and phone installation/collection, with one navigation exception.
  `/app_install/` opens the server file manager; selecting `index.html` opens
  the correct page. This is a user-reported result, not a new local browser or
  phone test; no detailed phone collection/HTTP/report trace was supplied.
- Adopted `http://ares.local/app_install/index.html` as the explicit page link
  in builder metadata, installer messages/checks and source guides. The current
  deployed page already exists at that address, so no host reinstallation or
  Nginx change is required for this link correction. Directory routing remains
  unchanged. Strengthened the post-install HTTP check to require the real page
  title, with a regression against an HTTP-200 file-manager response.
- Targeted Windows verification: 16 tests passed across the workflow, profiles,
  both-profile scaffold and fresh-ZIP fixture suites; all three changed shell
  scripts passed syntax checks. The scaffold fixture required the normal
  Windows user context after restricted Git Bash could not create its temporary
  output directory. Published source `6c5f2a74d52bf5b8d23f1d73f62096be3148ee29`
  passed all 87 native Ubuntu tests, including rejection of a successful file-
  manager response in the phone-page check, plus shell syntax checks:
  https://github.com/markknit/ares-usage-collection/actions/runs/41372477909.
- User will add the admin-module link at the end of its teacher section after
  confirming the direct address. No admin-module content was edited. A corrected
  release build must regenerate guides and package both this change and the
  storage-alias fix; existing ZIPs and PDFs were not changed by this source edit.

Still open:

- User's admin-module entry and remaining report attribution/support/reboot checks.
- Corrected ZIP, generated guides and independent release verification.
- Remaining deeper feature/repeat/failure checks and separate permanent-test or
  enabled optional-support acceptance.

### 2026-11-01 - Corrected test-copy installation completed on tsavo3

- Read the supplied terminal transcript referencing
  `/var/log/ares-offline-install-20261101_111100.log`; attachment SHA-256 is recorded
  in the [evidence note](offline-installer/docs/evidence/2026-11-01-v1.13-tsavo3-install.md).
  The actual test-server master completed all core stages after the extracted
  helper/manifests received the storage-alias correction. No new host commands
  or software tests were run by this documentation update.
- Package and Tsavo checks passed. Lesson3 was healthy and its installed corpus
  database counts were confirmed without re-import. Usage-export smoke test:
  18,703 bytes. Tsavo installation, content/link/mapping, portal/logo and video
  byte ranges passed; final Nginx/ARES/Lesson3/APK checks passed. Existing duplicate
  MIME warnings did not prevent Nginx validation or installer completion.
- Optional preparation succeeded and activation was declined with `n`; core
  success was retained. Recorded that preparation disabled legacy x11vnc, so
  remote-access preservation is not inferred from the successful core result.
- Updated acceptance rows to reflect actual server evidence. Preserved the
  distinction between this corrected existing-server extraction and the original
  ZIP, which still contains the old helper. No corrected ZIP was built or
  independently verified, and no field rollout was approved.

Still open:

- Client browser/video/PDF and phone collection/tracking tests.
- Existing support access and reboot/autostart/firewall persistence.
- Corrected release ZIP and independent verification before field rollout.
- Remaining repeat/failure/feature checks and separate permanent-test/optional
  enabled remote-support acceptance.

### 2026-11-01 - tsavo3 test installation and storage-alias correction

- User confirmed tsavo3 has always been a test server. The first attempt stopped
  when Docker could not create the Lesson3 bridge: its DOCKER filter chain was
  missing. Later diagnostics showed the separate ARES Internet lockdown plus
  extra default-drop rules in the iptables-managed IPv4 filter table. Supplied a
  targeted backup/removal/Docker-restart procedure retaining the ARES lockdown;
  the subsequent install log establishes Lesson3 readiness, not persistent
  firewall configuration or full support-network acceptance.
- Read the supplied `ares-offline-install-20261101_105039.log`: Lesson Plan,
  tracking mappings, usage-export smoke test and teacher APK deployment passed;
  Lesson3 was healthy and the administrator-guided importer reported 95 plans /
  806 lessons with installed status. Step 7 failed on `/mnt/sda3` parent checking
  before Tsavo staging/publication. Field/client/phone gates remain Pending.
- Corrected the Tsavo helper to resolve the configured storage anchor before
  strict destination checks. Added install/repeat/rollback, alternate-root
  confinement and below-anchor symlink regression coverage. Targeted Windows
  source/content/workflow/ZIP-fixture suite: 27 passed, two native-link checks
  skipped. Documented offline correction tested, including unchanged-package
  verification, exact three-file updates, backups and rejection of unrelated
  package damage. Published source `f93cb51d4aeb236936c52660013edcd541bab85e`
  passed all 86 native Ubuntu tests, including actual storage symlinks and
  below-anchor rejection, plus shell syntax checks:
  https://github.com/markknit/ares-usage-collection/actions/runs/41339985198.
- Documented an offline, exact-version correction for only the extracted test
  helper and two containing manifests, with backups outside the package. The ZIP
  and v1.12 remain unchanged. Host rerun and corrected release qualification are
  still required; the existing ZIP is not approved for field rollout.

### 2026-10-31 - Production v1.13 verified and promoted

- Recorded the operator's successful final tsavo3 resume at source `487dea0`:
  whole-package, APK/profile, release/images/corpus, TsavoTrust, remote-payload,
  fresh-ZIP and inherited-file checks passed. There are 313 ZIP files and all
  133 approved inherited files; one text file used normalized-newline comparison.
- The existing ZIP was reused unchanged, retaining SHA-256
  `1f0993a806b41aa7024e0f4af7e634e7186f9d08983669a88d91c45a93b692c9`,
  and promoted to `ARES_Q4_Update_offline_v1.13`. Added an artifact record linking
  its identity, assembly/correction/qualification commits and retained evidence.
- Final qualification source passed all 82 Ubuntu fixture tests; no further
  software tests or artifact rebuilds were needed for this documentation update.
- No live installer ran. Preserved prior evidence and v1.12 identity; the
  production-baseline branch remains separate from the simplification branch.

Still open:

- Offline installation and client/phone/content checks on a disposable server.
- Live field acceptance and rollout approval; optional remote acceptance when used.
- Permanent-test artifact build/acceptance remains separate from this production run.

### 2026-10-31 - Align inherited text comparison with its sealed newline convention

- User reports the resumed candidate passed whole-package, component and fresh-ZIP
  checks (313 files). Candidate SHA-256:
  `1f0993a806b41aa7024e0f4af7e634e7186f9d08983669a88d91c45a93b692c9`.
  The last inherited-file step then stopped at the raw-size assertion for
  `lesson_plan/payload/PDF/index.html`. It was not promoted or installed.
- Found an inconsistent comparison: B2 records normalized inherited text, while
  the final check compared raw output size/hash. Read-only inspection of the
  retained v1.11 source and v1.12 ZIP shows this HTML file has 1,057 CRLF endings:
  52,822 raw bytes versus 51,765 with LF endings. No source/artifact bytes changed.
- Compare inherited files directly from the verified ZIP, normalizing only the
  approved text/shell newline conventions. Do not normalize aliases or other
  content; binary comparisons remain exact. Collect all discrepancies in one
  report, and record actual inherited-file hashes plus the comparison used.
- Resume now preserves the existing ZIP bytes when its integrity helper is
  already current. This fix changes neither the staged HTML nor the helper, so
  the retained verified candidate can be reused without repackaging. All release
  checks and the inherited gate still precede promotion.
- Four disposable resume workflow tests passed, including CRLF approval matching,
  unchanged ZIP bytes, preservation of raw HTML bytes, content-change rejection,
  and no promotion after a failed check. All 20 shell syntax checks passed.
  Final inherited qualification and field acceptance remain Pending on tsavo3.

### 2026-10-31 - Correct Docker saved-image link verification

- The supplied tsavo3 terminal transcript confirms that the simplified-r3 builder
  completed its downloads, image save and candidate ZIP creation, then stopped in
  independent verification with `Unsafe or malformed payload archive` for the
  saved-image TAR. Root package integrity passed. The candidate was not promoted
  and no live installer ran.
- Reproduced the strict-checker rejection by read-only inspection of the retained
  v1.12 ZIP's image TAR: it contains two valid relative symlinks to a shared layer.
  No v1.12 bytes were changed. The prior tiny fixtures used regular layer files
  and did not cover this real Docker-save representation.
- Allow internal symbolic/hard links only in Docker saved-image archives. Resolve
  them from TAR metadata to existing regular members, retaining config identity,
  platform, tag and layer checks. Other payloads retain their existing type checks.
  Diagnostics now identify an unsupported member rather than only its archive.
- Added an explicit `--resume` path for the failed ed5052a simplified-r3 candidate:
  check the retained stage, preserve the old ZIP/manifest/helper, update the one
  integrity helper, reseal/repackage the same payload and rerun independent and
  inherited-file verification before promotion. No payload downloads, Docker
  pulls, image saves, source normalization or host installation are performed.
  Fixed the duplicate generic error message from parent/subshell traps.
- Local validation: all 11 component/release tests and all 20 shell syntax checks
  passed, including TAR symlink/hard-link fixtures and missing/cyclic/escaping
  targets. The corrected link resolver also resolves the real v1.12 shared-layer
  links to regular members using archive metadata only. Both disposable resume
  workflow tests passed: original ZIP retention, no builder invocation, unchanged
  inherited bytes, success-only promotion and no promotion after verification
  failure. Full v1.13 verification
  and field acceptance remain Pending until the retained candidate is resumed.

### 2026-10-31 - Simplify offline installation for technicians

- Created this separate clone/branch from `728741b`; preserved the original local
  checkout, tsavo3 C1 source/evidence and v1.12 artifact. No host installer ran.
- The technician runs `sudo bash install_offline.sh ARES-S00XX`, follows the existing
  Lesson3 administrator prompts, and checks the final message/local browser pages.
  Removed the separate preflight command and recovery-mode instructions from the
  technician guide. Full builds regenerate the printed guides from these sources.
- Removed the root-checksum bypass controller, wrapper and metadata receipt system.
  Keep one automatic root hash/inventory check; move detailed component validation
  to an automatic build-side verifier using a fresh ZIP extraction. Retained local
  checks in standalone utilities and Tsavo copy/rollback/HTTP verification.
- Added `offline-installer/run_tsavo3_build.sh` as the single C1 continuation:
  reuse the existing source seal, build in a fresh hidden area, automatically
  verify the ZIP and 133 approved inherited files, record final classification,
  and promote only after all checks pass. An existing output is never replaced.
- Moved remote preparation after successful core installation. Missing Ubuntu/
  desktop/SSH prerequisites, an occupied VNC port, or preparation failure produces
  an optional-support warning without failing the completed core installation.
  Existing active remote support is left in place when the port is occupied.
- Windows fixture validation: 72 tests run, 71 passed, one native POSIX-link test
  skipped. Tests cover real package rejection before host stages, core failure,
  remote-preparation failure preserving success, both-profile packaging and fresh
  ZIP verification. Host-changing stages, Debian metadata and Windows rsync/link
  operations are substituted fixtures, not real Ubuntu/field acceptance.
- Follow-up workflow/release and script-relative Tsavo tests passed (seven tests);
  all 20 remaining shell scripts passed syntax checks. The Tsavo launcher disables
  Python bytecode writes so repeat installation does not create unlisted cache
  files in the sealed package. Configuration is read only after the package check.
- Ubuntu CI passed all 75 tests with no skips for implementation commit
  `52b3b52ac269dba39f70b71d9b00c95dc38fe92c`, including native corpus-status and
  POSIX-link fixtures plus shell syntax. See
  [GitHub Actions run 41269118078](https://github.com/markknit/ares-usage-collection/actions/runs/41269118078).
  This is software/fixture evidence, not a live installation or the full
  production build. The new tsavo3 continuation has not been executed.
- Published `simplify-offline-install` separately. Confirmed the qualified
  `production-baseline-cleanup` branch still points to `728741b`; no merge was
  performed. Full production build and offline installation/client acceptance
  remain Pending. No verified artifact has been promoted.

### 2026-10-31 - Native Linux fixture validation evidence

- Recorded Ubuntu 24.04.2 LTS x86_64 validation on tsavo3 for
  `350690ffea893d3563d58c9505d8c2669c63cab8`: 24 shell checks, 87 unprivileged
  Python tests, three root corpus-status tests, native portal/PHP fixtures and
  POSIX symlink behavior passed; repository remained clean. See
  [evidence record](offline-installer/docs/evidence/2026-10-31-v1.13-linux-fixture-validation.md).
- Independently recomputed external archive SHA-256
  `022ab1eb15c71c5b6968f5fcd09c141daadf64fc0163e8e47913942df31a09e0`
  and checked all four archived log hashes against the supplied summary. Read
  evidence without extracting it; did not rerun tests or commit raw logs/archive.
- Supplemental real-PTY operator fixture rejected wrong confirmation, permitted
  exact-confirmation root-mismatch recovery and blocked component tampering.
  Complete workflow coverage was inline, not a committed reproducible test;
  adding Linux/root PTY regression coverage to CI remains Pending.
- Full v1.13 build and independent artifact verification, graphical installation,
  fresh-server clean install, real TigerVNC password generation, packaged `:1`,
  enrolled Tailscale repair, Tailscale-path SSH/VNC, reboot/autostart,
  disable/re-enable, partial-failure cleanup, browser playback and tracking
  attribution all remain Pending. No live profile gate passed. Preserved v1.12
  evidence and existing untracked files; documentation only, no build or push.

### 2026-10-30 - Explicit root-checksum recovery installer

- Added `install_offline_no_root_sha.sh` and a script-relative controller. Actual
  terminal input and exactly `INSTALL UNVERIFIED PACKAGE` are required before
  installation. No yes option or normal-installer/environment bypass was added.
  The controller reuses the unchanged normal workflow with one private preflight
  dispatch. Only root manifest content verification is skipped; its file must
  still exist. Warnings identify the result as NOT FULLY VERIFIED before and after.
- Shared preflight validates approved APK identity/profile, Lesson3 release,
  images and corpus, TsavoTrust, Tailscale, TigerVNC, required files and LFS pointers.
  Builder output now includes independent teacher-app, image and Lesson Plan
  manifests and the packaged APK verifier/approval record. Root SHA256SUMS covers
  recovery code and nested manifests while excluding only itself.
- Metadata-only recovery audit/receipts record UTC time, available operator,
  intentional root omission and outcome without interactive secrets. Standard
  receipts record verified preflight only; recovery completion never means full
  package verification or field acceptance.
- Windows validation: 72 tests ran, 70 passed, two native tests skipped (PTY and
  POSIX link). Covered both profiles, builder manifest inventory, component
  tampering/malformed payloads/missing files, root mismatch and confirmation,
  receipts, TsavoTrust and remote-support regressions. All 20 shell syntax checks
  passed. Linux-only corpus-status (three) and school-server integration (nine)
  tests were not run; actual dpkg metadata, root execution, host installation,
  receipt permissions and native PTY/link behavior remain Pending locally.
- Preserved `install_offline.sh` byte-for-byte, v1.12 ZIP/evidence and existing
  untracked files. All production/test live acceptance, packaged remote-support
  lifecycle, full v1.13 build/independent verification and field approval remain
  Pending. No final v1.13 ZIP built and no push performed for this step.

### 2026-10-30 - Optional remote-support corrections for v1.13

- Implemented the approved partial-failure policy as a separate step after
  TsavoTrust commit `32634eb`. TigerVNC failure after Tailscale/SSH readiness
  returns 2, diagnoses before stopping the owned VNC unit, retains the command-line
  path/identity/confirmed hostname and prints the retry command. Unresolved display
  ownership does not authorize stopping another user's unit. The optional core
  wrapper distinguishes partial failure, deferral and other errors while keeping
  successful core installation intact.
- Enrollment explains server outbound Internet and off-network cellular-phone
  browser approval. Auth output goes to `/dev/tty`, bypassing both log pipelines;
  diagnostics additionally redact URLs. The 120-second CLI timeout is bounded by
  an outer 125-second deadline plus five-second kill grace. Offline/timeout/deferred
  paths return 3 and print `sudo ares-enable-remote-access`. Connected enrollment
  is reused; no logout, forced reauthentication or identity deletion is performed.
- Added validated non-secret active/enabled baselines for `ssh.service` and
  `ssh.socket`, preserved over retries and restored by disable. Socket-activated
  Ubuntu behavior, static/runtime states and conservative legacy-record migration
  have fixture coverage. No saved file is evaluated as shell code.
- Added hidden, matching 6-8-character password prompts with three attempts,
  one normal eight-byte `tigervncpasswd -f` record and no view-only dialogue.
  Corrected `$AlwaysShared`, installed per-user `Xtigervnc-session` using a separate
  dbus-run-session/Cinnamon 2D session, and require three consecutive active/
  loopback-only samples. No physical GNOME/AnyDesk process/service is modified.
- Ran with bundled Python 3.12 (`PYTHONPATH=tests`):
  `python -X utf8 -B -m unittest test_remote_support test_profiles test_bundle_profiles test_offline_installer.OfflineInstallerSourceTests test_tsavo_content test_tsavo_install -v`.
  Result: 60 run, 59 passed, one native POSIX-link test skipped. Windows filesystem
  transaction fixtures still substitute link operations; service/network/password
  tests use stubs and are not live acceptance.
- Additional Windows checks passed: six incoming-processor tests (Python launcher
  adapted to the bundled executable, Git coreutils on PATH), static portal tests
  with UTF-8 mode, and shell syntax for all 19 scripts. Not run on Windows: three
  Linux/root corpus tests and nine Linux school-server installer fixtures. Native
  systemd/Tailscale/TigerVNC, interactive terminal and client tests remain Pending.
- Verified the v1.12 ZIP hash remains
  `fef897456108b70664fae280e4d3e4de354be23d3e0acbe4dc313dc1b458cd4a`;
  dated evidence is unchanged. No final v1.13 field ZIP was built and no root-
  checksum-bypass implementation was started. Lesson3 v0.94 and pinned offline
  remote binaries remain unchanged.

Still open:

- All packaged `:1`, Tailscale-path SSH/VNC, physical-session coexistence,
  enrollment/log privacy, reboot/autostart, disable/re-enable and partial-retry
  acceptance checks for both profiles remain Pending.
- All other unperformed live installation, TsavoTrust, Lesson3 and rollout gates
  remain Pending. Stop after the dedicated remote-support commit; no push.

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
