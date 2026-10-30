# Production and permanent test profiles

Production is the default and uses `ares.local`. The permanent test package uses
`ares-test.local`. Existing online-demo configuration is not deployed or changed.
Build separate sealed bundles; do not edit a field package after SHA256SUMS is made.

```bash
bash build_offline_bundle.sh --source /path/to/source --output /path/to/output --profile production
bash build_offline_bundle.sh --source /path/to/source --output /path/to/output --profile test --apk /path/to/approved-test-profile.apk
```

`package.conf` is the canonical approved release/profile manifest. All runtime
entry points read it; environment overrides cannot silently change a sealed
profile. The mDNS alias is independent of Linux/Tailscale hostname and school code.
Test uses a distinct bundle suffix and separate Android application identity.

Avahi publishes the selected alias using an eligible LAN IPv4 address. Nginx
replaces only the two ARES profile aliases and preserves other server names.
An existing separately configured online demo remains on its production profile.
Do not activate both profiles on the same server or deploy either over the demo.

Lesson3 `ADMIN_URL` uses the selected alias and port 3001. In upstream v0.94,
`SERVER_URL` enables strict public posture, including empty-user boot refusal.
The canonical manifest explicitly keeps it empty for both offline HTTP profiles,
as required by the packaged upstream `.env.example`. This parameter is checked
alongside ADMIN_URL; changing the public security posture needs a separate review.
A healthy existing deployment with different URLs/version is refused rather than
silently migrated or overwritten.

The builder renders static HTML/HTML fragments, teacher pages, JS, JSON and
Markdown links, including encoded tracker targets, before checksum generation.
Collection/export server endpoints use relative paths; central HTTPS upload and
school identity are independent of this alias. Existing public school JSON examples
remain production examples. Generate test fixtures using
`tools/build_school_assets.py --server http://ares-test.local` in an isolated root.

Android builds:

```bash
gradle -p android/ares-sync :app:assembleDebug
gradle -p android/ares-sync :app:assembleDebug -ParesProfile=test
```

Production uses `org.areseducation.sync`; test uses `org.areseducation.sync.test`.
Collection and reachability URLs compile from the selected host. Cleartext is
allowed only for that profile's literal domain in network-security XML.
The builder rejects APKs containing the other profile's collection endpoints.
Use a reviewed signed test APK for an actual field/test package; locally built
debug APKs are not production-approved releases.

Bundled PDF references currently retain production URL examples. Use the rendered
profile Markdown guides and actual teacher pages for test-profile URLs. This is a
known documentation limitation, not evidence of complete test-profile acceptance.
See `LOCAL_ALIAS_AUDIT.md` for every tracked text occurrence and `PROFILE_ACCEPTANCE.md`
for remaining physical/client/target gates.

Tsavo is excluded from core installation and from inherited source copying. Its
absent installer cannot fail core installation. No checksum-bypass wrapper is copied.
