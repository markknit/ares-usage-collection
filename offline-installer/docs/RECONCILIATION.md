# Target snapshot reconciliation, 2026-10-29

Baseline: fetched and fast-forwarded from f2d2598 to published
5ac6911a24e93381d5f54150e1d897453bf41936 before implementation. No tracked local
changes existed. Untracked Android wrapper/configuration/build files and the
empty `-Destination` file were preserved. Nothing was deployed to the online demo.

The three published commits add v0.94/v1.11, its guide and acceptance checklist,
fix archive validation under pipefail, and remove stale generated payloads.
All are retained. Windows checkout CRLF broke existing rollout checksum checks;
release text now has explicit LF attributes without weakening checksum tests.

Snapshot: `C:/Users/MRKni/OneDrive/ARES Utilities/target-server-snapshot-2026-10-29`.
It contains only `install_offline.sh`, `remote-access/activate_ares_remote_support.sh`
and `README.txt`. It cannot establish three-way edit ancestry or server state.
Its README reports shell syntax/static checks, without runtime logs. Preserve the
post-core optional activation design, school-name prompt, and standard OpenSSH
transport. Do not adopt its missing unconditional Tsavo dependency, hosts-file
escaping defect, missing failure rollback, or unchecked display reassignment.

## Sealed profiles and approved release

`package.conf` owns the approved Lesson3 version and selected profile. Runtime
scripts source the packaged configuration rather than embedding release literals.
Build with `--profile production` (default, `ares.local`) or `--profile test`
(`ares-test.local`). The test package has a distinct filename. Profile aliases
never derive from Linux or Tailscale hostnames. No live demo is changed.

The builder renders inherited HTML, HTML fragments, JS, JSON and Markdown URLs
before generating checksums. Production-reference PDFs remain byte-identical;
their production URL examples must be interpreted using the profile guide.
The existing source package is still required for lesson PDF payloads and assets.

Android: use `-ParesProfile=test` for the isolated `org.areseducation.sync.test`
application; production remains `org.areseducation.sync`. Each profile compiles
its collection/probe URLs and cleartext-domain resource. The test builder requires
an explicitly supplied matching APK, and the builder checks compiled DEX endpoints
for both profiles. A debug build is validation evidence, not an approved field APK.
Central HTTPS upload/enrollment destinations and collection schedules are unchanged.

## Validation gates

Software checks and live target/client acceptance are distinct. No unattended
activation, credentials, hostname changes, deployment, or corpus import is performed
from this Windows checkout. The live acceptance matrix will remain pending until
actual Ubuntu server, phone, client-resolution and desktop evidence is recorded.
