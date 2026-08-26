# ARES Sync Android MVP

ARES Sync is the replacement for the Automate/legacy-extension phone workflow.

## Validated pilot results

On the real pilot Android API 36 phone and tsavo3 server:

- manual connection to `ARES2` followed by **Test current Wi-Fi connection** reaches `ares.local`;
- the scheduled collection endpoint returns HTTP 200;
- collection metadata is returned;
- the usage CSV downloads successfully into app-private pending storage; and
- the phone reports that concurrent local-only Wi-Fi is not supported.

This validates the real `ARES2 -> ares.local -> scheduled endpoint -> CSV -> app-private storage` path independently of Wi-Fi switching.

The API 30 `WifiNetworkSpecifier` compatibility experiment was also tested on the real phone. Android returned the request as unavailable and did not disconnect the primary Wi-Fi or connect to `ARES2`. That path is therefore considered unsuccessful on the pilot device.

## Current experiment: API 28 direct Wi-Fi control

Android's `WifiManager` compatibility documentation states that legacy methods including `disconnect()`, `enableNetwork()`, `reconnect()`, and full configured-network access are forced to fail for ordinary apps targeting Android 10 / API 29 or higher. This build temporarily targets API 28 to test the remaining legacy compatibility path directly.

The build keeps `compileSdk = 36` but uses `minSdk = 28` and `targetSdk = 28` for this controlled test. It is not intended for Google Play distribution.

The **Test automatic ARES2 switch** button now attempts to:

1. record the phone's current Wi-Fi network ID and SSID;
2. locate the saved open `ARES2` configuration, or add it if Android permits;
3. call the legacy Wi-Fi disconnect / enable / reconnect controls;
4. wait until Android reports `ARES2` as the connected SSID;
5. obtain the active Wi-Fi `Network` and run the already-validated `ares.local` download test;
6. request restoration of the previously connected Wi-Fi network; and
7. report an additional status check eight seconds after restoration is requested.

The UI reports the return values from the legacy APIs so a failed device test can distinguish configured-network access, disconnect, enable, reconnect, association, and restore failures.

The **Test current Wi-Fi connection** button remains available as the validated manual diagnostic path.

## Acceptance test

Start with the phone connected to a normal saved Internet Wi-Fi network and `ARES2` available nearby. Tap **Test automatic ARES2 switch**.

A successful API 28 experiment requires:

- the legacy Wi-Fi API calls return success;
- the phone leaves the original Wi-Fi and associates with `ARES2`;
- the ARES endpoint returns HTTP 200 or 204;
- a due CSV is saved when HTTP 200 is returned;
- ARES Sync requests restoration of the prior saved Wi-Fi; and
- the eight-second status check shows the phone back on the prior Wi-Fi without manual intervention.

If the legacy APIs return failure or Android does not switch, ordinary sideloaded-app Wi-Fi control will be treated as exhausted for this pilot device and the architecture should move to a managed/device-owner or network-design alternative.

## Build

Open `android/ares-sync` as a project in Android Studio and build the `app` module. This experiment uses JDK 17 and compiles against Android API 36.

## Distribution caveat

The API 28 target deliberately uses legacy compatibility behavior and does not satisfy current Google Play target-SDK requirements. This is an ARES-controlled sideloaded-device experiment only.

## Security

- No Wi-Fi passwords, API credentials, OAuth tokens, or school-private data belong in this repository.
- `ARES2` is currently an open local network, so no Wi-Fi credential is embedded in the app.
- Cleartext HTTP is permitted only for the local hostname `ares.local`; future central upload traffic must use HTTPS.
