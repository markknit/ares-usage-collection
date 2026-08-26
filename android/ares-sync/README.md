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

The API 28 direct `WifiManager` compatibility experiment was then tested on the same phone. Android exposed two configured networks and identified saved `ARES2` as network ID 1. The calls to `disconnect()`, `enableNetwork()`, and `reconnect()` all returned `true`, and the corresponding restore calls also returned `true`. Despite those return values, Android never associated with `ARES2` before the timeout. The app then observed the phone back on its previous `AndroidWifi` network.

Therefore ordinary sideloaded-app automatic Wi-Fi switching is considered exhausted on this pilot Android 16 / API 36 device. The remaining problem is platform-controlled Wi-Fi association, not ARES server reachability, DNS, endpoint execution, CSV generation, saved-network discovery, or app-private storage.

## Wi-Fi experiments completed

### API 36 local-only request

The phone reports `Concurrent local-only Wi-Fi: false`, so the modern secondary local-only Wi-Fi request cannot be satisfied on this device.

### API 30 `WifiNetworkSpecifier` compatibility test

The exact open `ARES2` request returned unavailable. Android did not perform the documented legacy primary-Wi-Fi handoff on this pilot device.

### API 28 direct `WifiManager` test

The app successfully:

1. read the saved network list;
2. found `ARES2` as network ID 1;
3. remembered the prior Wi-Fi;
4. received `true` from legacy disconnect / enable / reconnect calls; and
5. received `true` from the restore calls.

However, Android did not actually associate with `ARES2` before timeout. A `true` return from these deprecated APIs therefore does not provide a reliable automatic network switch on the pilot Android 16 device.

## Architecture implication

Do not spend additional MVP time trying ordinary-app Wi-Fi switching variants on this phone. The validated download path should be retained, but unattended collection now requires a different connection strategy.

The leading alternatives are:

1. provision ARES Sync as a managed/device-owner application so it has privileged Wi-Fi control;
2. change the ARES network design so the phone can remain connected to `ARES2` while still reaching the Internet, removing the need to switch networks; or
3. accept a user-assisted Wi-Fi handoff and automate only the collection/download/upload steps around it.

A larger transport redesign such as Bluetooth should be considered only if the simpler managed-device or network-design options are not viable.

## Build

Open `android/ares-sync` as a project in Android Studio and build the `app` module. The current diagnostic branch used JDK 17 and compiled against Android API 36.

## Distribution caveat

The low target-SDK builds were ARES-controlled compatibility experiments and do not satisfy current Google Play target-SDK requirements. They are not intended as Play Store release configurations.

## Security

- No Wi-Fi passwords, API credentials, OAuth tokens, or school-private data belong in this repository.
- `ARES2` is currently an open local network, so no Wi-Fi credential is embedded in the app.
- Cleartext HTTP is permitted only for the local hostname `ares.local`; future central upload traffic must use HTTPS.
