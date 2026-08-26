# ARES Sync Android MVP

ARES Sync is the replacement for the Automate/legacy-extension phone workflow.

## Current experiment: Android Wi-Fi switching

The pilot Android 16 / API 36 phone reports that concurrent local-only Wi-Fi is not supported. An API 30 `WifiNetworkSpecifier` compatibility experiment was tested because Android documents legacy behavior for apps targeting Android 11 / API 30 or lower, where the primary Wi-Fi may be disconnected before a requested local/peer Wi-Fi connection is established.

The API 30 experiment did not work on the pilot phone. With the phone connected to a normal Internet Wi-Fi network, Android returned `onUnavailable()` for the exact open `ARES2` request and did not perform a primary-Wi-Fi handoff.

A separate current-network test was successful. While manually connected to `ARES2`, ARES Sync reached `http://ares.local/tracker/prepare_due_usage_upload.php`, received HTTP 200, and saved the returned usage CSV into app-private pending storage.

## Validated pilot result

On 2026-08-25, the **Test current Wi-Fi connection** path was validated on the real pilot Android API 36 phone while manually connected to `ARES2`:

- `ares.local` was reached successfully;
- the scheduled collection endpoint returned HTTP 200;
- collection metadata was returned;
- a 26,561-byte usage CSV was downloaded successfully; and
- the file was saved into ARES Sync app-private pending storage.

This proves the real `ARES2 -> ares.local -> scheduled endpoint -> CSV -> app-private storage` integration.

On the same phone, the **Test automatic ARES2 switch** path failed with:

- Android API: 36;
- app target SDK: 30;
- Wi-Fi enabled: true;
- concurrent local-only Wi-Fi: false;
- exact `ARES2` match; and
- Android unable to satisfy the switch request.

Therefore the unresolved problem is specifically automatic Wi-Fi switching on the pilot phone, not server reachability, DNS, endpoint execution, CSV generation, or app-private file storage.

## Next compatibility experiment

Before redesigning the transport architecture, test a controlled-deployment build targeting Android 9 / API 28 that uses the legacy `WifiManager` network-control APIs. Android documents that `disconnect()`, `enableNetwork()`, `reconnect()`, and related configured-network operations are forced to fail for apps targeting Android 10 / API 29 or higher, while lower-target apps remain exempt. This is a sideload-only compatibility experiment, not a Play Store configuration.

A successful API 28 test must prove that ARES Sync can:

1. identify or add the open `ARES2` Wi-Fi configuration;
2. disconnect the current Wi-Fi;
3. connect to `ARES2` without manual intervention;
4. reach the ARES endpoint and download the due usage CSV;
5. disconnect/release `ARES2`; and
6. reconnect to the prior saved Internet Wi-Fi automatically.

## Build

Open `android/ares-sync` as a project in Android Studio and build the `app` module. The project requires Android 10 / API 29 or newer at runtime and JDK 17. Experimental target SDK values are used only to test Android Wi-Fi compatibility behavior on the controlled pilot device.

## Distribution caveat

Low target-SDK builds are ARES-controlled deployment compatibility experiments and do not satisfy current Google Play target-SDK requirements. They are not intended as Play Store release configurations.

## Security

- No Wi-Fi passwords, API credentials, OAuth tokens, or school-private data belong in this repository.
- `ARES2` is currently an open local network, so no Wi-Fi credential is embedded in the app.
- Cleartext HTTP is permitted only for the local hostname `ares.local`; future central upload traffic must use HTTPS.
