# ARES Sync Android MVP

ARES Sync is the replacement for the Automate/legacy-extension phone workflow.

## Current experiment: API 30 Wi-Fi switching

The pilot Android 16 / API 36 phone reports that concurrent local-only Wi-Fi is not supported. Android documents different `WifiNetworkSpecifier` behavior for apps targeting Android 11 / API 30 or lower: the primary Wi-Fi network is disconnected before the requested local/peer Wi-Fi connection is established.

This build therefore keeps `compileSdk = 36` but temporarily uses `targetSdk = 30` to test whether Android can:

1. leave the phone's current Internet Wi-Fi;
2. connect to the open `ARES2` SSID using `WifiNetworkSpecifier`;
3. reach `http://ares.local/tracker/prepare_due_usage_upload.php`;
4. download the due usage CSV into app-private storage;
5. release the ARES2 request; and
6. automatically reconnect the phone to its prior Internet Wi-Fi.

The automatic test restores exact `ARES2` matching. Because this build targets API 30, it requests `ACCESS_FINE_LOCATION` at runtime as required by Android's pre-Android-13 Wi-Fi permission model.

A second **Test current Wi-Fi connection** button is included as a diagnostic fallback. If the automatic switch fails, manually connect the phone to `ARES2`, return to the app, and use that button to verify the `ARES2 -> ares.local -> CSV` path independently of Wi-Fi switching.

## Validated pilot result

On 2026-08-25, the **Test current Wi-Fi connection** path was validated on the real pilot Android API 36 phone while manually connected to `ARES2`:

- `ares.local` was reached successfully;
- the scheduled collection endpoint returned HTTP 200;
- collection metadata was returned;
- a 26,561-byte usage CSV was downloaded successfully; and
- the file was saved into ARES Sync app-private pending storage.

This proves the real `ARES2 -> ares.local -> scheduled endpoint -> CSV -> app-private storage` integration. Automatic switching away from and back to the phone's normal Internet Wi-Fi remains the unresolved MVP test.

## Acceptance test

Start with the phone connected to a normal saved Internet Wi-Fi network, then tap **Test automatic ARES2 switch**. A successful test requires:

- Android supplies an ARES2 network to the app;
- the ARES endpoint returns HTTP 200 or 204;
- a due CSV is saved when HTTP 200 is returned;
- ARES Sync releases its ARES2 request after the server test; and
- Android reconnects to the prior Internet Wi-Fi without manual intervention.

Repeat the test a second time to determine whether Android requires another network approval prompt.

## Build

Open `android/ares-sync` as a project in Android Studio and build the `app` module. The project requires Android 10 / API 29 or newer and JDK 17.

## Distribution caveat

The API 30 target is an ARES-controlled deployment compatibility experiment and does not satisfy current Google Play target-SDK requirements. It is not intended as a Play Store release configuration.

## Security

- No Wi-Fi passwords, API credentials, OAuth tokens, or school-private data belong in this repository.
- `ARES2` is currently an open local network, so no Wi-Fi credential is embedded in the app.
- Cleartext HTTP is permitted only for the local hostname `ares.local`; future central upload traffic must use HTTPS.
