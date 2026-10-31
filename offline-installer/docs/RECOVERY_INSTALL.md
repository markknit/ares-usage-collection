# Authorized root-checksum recovery procedure

The normal field entry point remains `sudo bash install_offline.sh ARES-S00XX`.
Its script is unchanged, and its public preflight always verifies root SHA256SUMS
and component integrity. There is no environment switch or normal-installer flag
that silently disables root verification.

Use recovery only when an authorized technician deliberately modified a trusted
package (for example a reviewed installer/documentation patch), understands why
the root checksum no longer matches, and can still validate every component.
Do not use it for unexplained corruption, missing files, failed component hashes,
LFS pointers or an untrusted source. Checksums do not authenticate an untrusted
package whose checksums or validation code may also have been replaced.

## Explicit operator action

At an interactive Ubuntu terminal, from the extracted package:

```bash
sudo bash install_offline_no_root_sha.sh ARES-S00XX
```

After reading the warning, type exactly:

```text
INSTALL UNVERIFIED PACKAGE
```

Empty, wrong or whitespace-altered input is rejected. Piped/redirected stdin is
rejected even if it contains that phrase. There is no automatic-yes option. This
is an explicit accidental-bypass safeguard, not a security boundary against an
operator who can edit or manually execute package code.

Only verification of the bundle's **root `SHA256SUMS` contents** is skipped.
The manifest file must still exist. The following remain mandatory:

- All required files and target/host preflight checks.
- Approved APK hash/approval record, compiled profile endpoints, cleartext policy
  and application identity.
- Lesson3 release checksum, safe archive structure and v0.94 version.
- Independent Docker-image archive/reference checksums, archive structure, saved
  image tags and configuration identities matching the release.
- Pinned corpus inventory, per-file hashes, parseable schema and 95/806 counts.
- TsavoTrust component checksums, exact eight-file inventory, hashes and references.
- Tailscale archive checksum and executable binary structure.
- All four pinned TigerVNC Debian packages, checksums and dpkg-deb metadata.
- Lesson Plan payload and embedded ARES Sync rollout component manifests.

Existing component installers still perform their own checks. Recovery never
suppresses their failures. Do not edit a failed component manifest merely to make
damaged/unreviewed content pass. LFS pointers and malformed payloads still fail.

The connected builder creates the additional component manifests and packages
the APK verifier. School servers use their existing Python/coreutils/dpkg tools;
this procedure downloads nothing and installs no validation dependencies online.
Older v1.12 bundles lack this v1.13 recovery architecture; do not retrofit or alter
the verified v1.12 ZIP to use it.

## Warnings, logs and receipts

A prominent **NOT FULLY VERIFIED** warning appears before the workflow, during
preflight and in the final recovery summary. Recovery writes a root-only metadata
audit under `/var/log/ares-offline-recovery-*.log` and a receipt under
`/var/lib/ares/offline-installer/receipts/`. Both record intentional root-verification
omission, UTC timestamps, available operator name and outcome. The audit records
metadata only, not a duplicate interactive transcript or environment dump.

Verified preflight receipts identify `root_sha256: verified`, phase
`preflight_passed`, and **do not** claim installation completion. Recovery receipts
identify `root_sha256: intentionally_skipped`; the final phase records completed
or failed installation and exit status. Recovery always records
`fully_verified: false`. Successful component checks do not make the overall
recovered package fully verified or field accepted.

Do not record passwords, authentication URLs, tokens or other credentials in
receipts or support evidence. Existing hidden password prompts and terminal-only
Tailscale authorization remain unchanged. If recovery fails, preserve the metadata
receipt and investigate the specific component/host failure; root bypass cannot
repair it or roll back the entire multi-component workflow automatically.

## Shared workflow and release gates

The wrapper resolves its package relative to itself and invokes a Python controller.
After confirmation, that controller sources the unchanged normal installer in a
child shell, with one private, non-exported `bash` dispatch function for its exact
preflight call. That call runs the shared preflight in recovery mode. Every other
component command is executed normally. A changed preflight contract fails closed.
No separate copy of the full installation sequence is maintained.

The root manifest includes the recovery entry point, controller, validators and
nested component manifests, excluding only root SHA256SUMS itself. This means the
normal verified route also protects the recovery code as part of the package.

Native Linux TTY/root execution, end-to-end host preflight, actual recovered
installation, receipt permissions and all field acceptance remain **Pending**.
Windows tests mock the TTY boundary and host stages while exercising the shared
checksum/component validators. Native PTY coverage is configured for Linux CI.
No final v1.13 field ZIP is established by this source change. Preserve v1.12
artifact/evidence unchanged and complete [PROFILE_ACCEPTANCE.md](PROFILE_ACCEPTANCE.md).
