# Release checklist

## Android release package

- [ ] Production APK is a release-signed build, not a CI debug build.
- [ ] Signing keystore and passwords are stored outside the repository.
- [ ] Version name and versionCode are recorded.
- [ ] Source commit SHA is recorded.
- [ ] APK SHA-256 is recorded.
- [ ] Exact signed APK installs on a clean Android phone.
- [ ] Existing enrolled test phone can upgrade when expected.
- [ ] ARES logo and all four appearance modes render correctly.
- [ ] School search and school selector are readable in light and dark system modes.
- [ ] Keyboard does not cover school-search or enrollment-code fields.
- [ ] Notification permission flow works.

## Public setup portal

- [ ] Portal validation passes.
- [ ] HTTPS certificate is valid.
- [ ] `public/assets/downloads/ares-sync.apk` exists on the deployed site.
- [ ] Published APK SHA-256 matches the approved release hash.
- [ ] Download button works from an Android phone.
- [ ] Sideload instructions match the tested Android install flow.
- [ ] Teacher can recover from the "Allow from this source" prompt.
- [ ] Teacher guide does not require Round Sync, Automate, MacroDroid, rclone, or Google Drive setup.

## Enrollment and phone behavior

- [ ] School search returns the expected canonical school.
- [ ] Fresh one-time enrollment code succeeds.
- [ ] Reused enrollment code is rejected.
- [ ] Fresh mid-year enrollment baselines earlier scheduled periods correctly.
- [ ] Normal enrolled screen shows school, next collection, and no-action-required state.
- [ ] Due collection first attempts silent local collection.
- [ ] Teacher is prompted only when school Wi-Fi assistance is required.
- [ ] Pending file survives app/process interruption and phone restart as designed.
- [ ] Upload succeeds after later cellular or Wi-Fi internet access.
- [ ] Pending count returns to zero after central acknowledgement.

## School server

- [ ] Installer runs successfully on a clean/representative school server.
- [ ] Production collection schedule is installed and matches the Android release.
- [ ] Existing report builder completes successfully.
- [ ] State-aware no-due endpoint returns HTTP 204 when appropriate.
- [ ] Due endpoint returns a populated CSV when a collection is due.

## Central service and reporting

- [ ] HTTPS upload service accepts the release app's enrolled-device upload.
- [ ] Duplicate retry is idempotent.
- [ ] Protected incoming/data files are not publicly readable.
- [ ] Local incoming processor validates and archives accepted files once.
- [ ] Invalid files are quarantined.
- [ ] Exact-content duplicates are suppressed.
- [ ] Existing reporting command runs after newly accepted uploads.
- [ ] Known acceptance-test uploads are excluded or removed intentionally before production reporting.

## Operations and rollback

- [ ] Previous approved APK is retained privately for rollback.
- [ ] Previous server/deployment package is retained.
- [ ] Production deployment instructions are current.
- [ ] Teacher installation instructions are current.
- [ ] Technician installation instructions are current.
- [ ] Release/version/hash record is saved outside the public download directory.
- [ ] Autonomous Android alarm timing limitation is documented until independently field-validated.
