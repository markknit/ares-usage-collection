# Tsavo Trust in offline installer v1.13

Lesson3 remains v0.94. This change integrates TsavoTrust content; it does not
establish live installation, video playback, tracking or remote-support acceptance.
The verified v1.12 ZIP and its evidence are retained unchanged.

## Authoritative build source

The external source passed to `build_offline_bundle.sh --source` must contain:

```text
TsavoTrust/
  index.htmlf
  tsavo_trust_logo.jpg
  Videos/
    2025 Tt Community Program.mp4
    How Kenya’S Last Living Super Tuskers Are Escaping Poachers.mp4
    The Tsavo Trust.mp4
    Tsavo Trust 2025 Organisational Film.mp4
    Tsavo Trust Protecting The Big Tuskers   Cinematic Short Film.mp4
    Tt Rhino Clip.mp4
```

These are exactly eight files. Keep the curly apostrophe and the three spaces
before `Cinematic`. Extra source artwork, copy text and legacy installers belong
outside this normalized folder. Do not pass the previously nested snapshot as-is.
Normalize a separate build-source copy; preserve the original snapshot.

Git owns `manifests/tsavo-trust-source.json`, validation/deployment code and tests.
The external folder owns the media bytes. No MP4s or Git LFS pointers belong in
this repository. The pinned source page is the reviewed 2026-10-30 snapshot page;
the builder makes exactly three corrections in its staged copy: alternative text
`Tsavo Trust`, `Presented by`, and `data-module-id="TsavoTrust"`. Source files are
not edited. Unknown source hashes require deliberate review and a new pin.

Before touching build outputs, validation requires exact names, sizes, SHA-256
hashes, seven local asset references and valid MP4 box/sample structures (AVC
video/AAC audio). No `ffprobe` or new package is required on school servers.
Both full and scaffold builds require validated Tsavo input. Tests use a copied
builder with tiny explicitly pinned fixture media; scaffolds remain NOT_FIELD_READY.

## Tracking and portal evidence

Read-only comparison evidence:
`target-server-snapshot-2026-10-30/key_map.live-2026-10-30.csv`, SHA-256
`f560bb4a0f70da2bee029a7c86a6630aefe18180b89ea2d0c619a237ab80eab1`.
The live export uses `module:<directory name>` keys, includes
`module:OlpejetaConservancy,OPC,` and the three existing Lesson Plan mappings,
and contains no Tsavo mapping. The user confirmed comparable-module evidence for
the `www2/modules` link design before this implementation continued.

Deployment appends only `module:TsavoTrust,Tsavo Trust,` if absent. Every original
byte/entry is preserved, including historical Ol Pejeta mappings. An existing
conflicting or duplicate Tsavo key causes preflight failure; no wholesale key-map
replacement or historical data relabeling is performed.

Installed content: `/mnt/sda3/var/www/modules/TsavoTrust`.
Portal link: `/mnt/sda3/var/www/www2/modules/TsavoTrust`, pointing to that content.
The deployment never changes Nginx, mDNS, hostnames, school identity or APK profiles.

## Deployment, backups and recovery

Core installation runs packaged `tsavo/install.sh --host "$ARES_ALIAS"`, using
script-relative Python helpers and the generated content manifest. Preflight
checks source hashes, inventory, parent directories, mapping conflicts and free
space. Symlinked parents and special-file destinations are refused.

Deployment is serialized. It stages content on the destination filesystem, checks
the staged copy, applies directory/file modes 0755/0644 and ownership ares:www-data,
then publishes the module, mapping and link. Prior objects are retained as hidden
`.NAME.tsavo-backup-TOKEN` siblings on each object's filesystem, including existing
portal directories or links. They are not exposed as duplicate module cards.
Every run revalidates; repeating does not add another mapping.

On an exception, failed verification or handled termination signal, changed
objects are removed and prior objects restored in reverse order. Restore failures
are reported with retained backup paths for operator recovery. Keep backups until
acceptance. Sudden power loss/SIGKILL recovery and live installation remain Pending;
do not infer those from exception-path tests.

Verification checks installed paths, sizes/hashes, the exact portal link, mapping,
rendered `www2` portal card, logo delivery, and 206 byte-range responses for every
video through both the main module path and portal link. The selected profile alias
is supplied as the HTTP Host header; requests go to loopback without a proxy.
Failures prevent a successful installation result and trigger module rollback.

The package's `tsavo/SHA256SUMS` covers module helpers, manifest and payload.
Root `SHA256SUMS` covers all nested checksum manifests and excludes only itself.
Generate checksums after rendering; never bypass them. No v1.12 manifest is edited.

## Pending live acceptance - repeat for both profiles

- Clean offline install and safe repeat installation on disposable Ubuntu targets.
- Portal card/logo, all six videos, seeking/range delivery and browser playback.
- Correct Tsavo attribution through the actual tracking/report pipeline; unchanged
  historical Ol Pejeta mappings and reports.
- Existing-directory/link conflicts, failure restoration and interrupted recovery.
- All other [profile acceptance](PROFILE_ACCEPTANCE.md), Lesson3 UI/content and
  packaged remote-support gates remain Pending.
