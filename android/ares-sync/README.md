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

The API 28 direct `WifiManager` compatibility experiment was then tested on the same phone. Android exposed saved `ARES2` as network ID 1. The legacy calls to `disconnect()`, `enableNetwork()`, and `reconnect()` returned `true`, but Android did not associate with `ARES2` before timeout and returned to the previous `AndroidWifi` network.

A final forced-switch variant explicitly attempted to disable the prior `AndroidWifi` network before connecting to `ARES2`. On the real device the diagnostic result was `disablePrevious=false`, while `disconnect=true`, `enableNetwork=true`, and `reconnect=true`. Android therefore refused to remove the existing saved network from association candidates, and again never associated with `ARES2` before timeout.

Android's `WifiManager.disableNetwork()` documentation states that applications are not allowed to disable networks created by other applications. This matches the observed pilot behavior: ARES Sync can see the existing network configuration, but an ordinary sideloaded app cannot reliably suppress that network and force the handoff.

An Automate-specific ownership test was also performed. `ARES2` was first forgotten in Android settings, then Automate's **Wi-Fi network connect** block was configured to add `ARES2` itself and request an **Exclusive** connection. The test was run twice on the same Android 16 / API 36 phone and failed both times. Therefore Automate ownership of the ARES2 configuration does not provide a practical automatic-switch workaround on this pilot device.

Therefore ordinary sideloaded-app automatic Wi-Fi switching is considered exhausted on this pilot Android 16 / API 36 device. The remaining problem is platform-controlled Wi-Fi association, not ARES server reachability, DNS, endpoint execution, CSV generation, saved-network discovery, Automate ownership, or app-private storage.

## Wi-Fi experiments completed

### API 36 local-only request

The phone reports `Concurrent local-only Wi-Fi: false`, so the modern secondary local-only Wi-Fi request cannot be satisfied on this device.

### API 30 `WifiNetworkSpecifier` compatibility test

The exact open `ARES2` request returned unavailable. Android did not perform the legacy primary-Wi-Fi handoff on this pilot device.

### API 28 direct `WifiManager` test

The app successfully:

1. read the saved network list;
2. found `ARES2` as network ID 1;
3. remembered the prior Wi-Fi;
4. received `true` from legacy disconnect / enable / reconnect calls; and
5. received `true` from the restore calls.

However, Android did not actually associate with `ARES2` before timeout. A `true` return from these deprecated APIs therefore does not provide a reliable automatic network switch on the pilot Android 16 device.

### API 28 forced prior-network disable test

The app then attempted to call `disableNetwork()` on the prior `AndroidWifi` configuration before enabling `ARES2`. The real device returned:

- `disablePrevious=false`;
- `disconnect=true`;
- `enableNetwork=true`;
- `reconnect=true`;
- timeout before `ARES2` association; and
- final observed SSID `AndroidWifi`.

This closes the ordinary-app direct-control path for the pilot phone.

### Automate-owned ARES2 exclusive-connect test

To test whether Automate could gain additional control by owning the network configuration, `ARES2` was removed from Android's saved networks and Automate was configured to add the open `ARES2` network itself using **Wi-Fi network connect** with **Add network: Yes** and **Exclusive: Yes**. The test failed twice and did not produce a working automatic handoff to `ARES2`.

This closes the Automate-based automatic-switch workaround for the pilot phone as well.

## Architecture implication

Do not spend additional MVP time trying ordinary-app or Automate Wi-Fi switching variants on this phone. The validated download path should be retained, but unattended collection now requires a different connection strategy.

The leading alternatives are:

1. provision ARES Sync as a managed/device-owner or other qualifying device-policy application with privileged Wi-Fi control;
2. change the ARES network design or operating procedure so the phone is already connected to `ARES2` when collection occurs, eliminating the need for the app to force a switch;
3. use a different local transport, such as Bluetooth, for server-to-phone collection while leaving the phone's normal network connection alone; or
4. accept a user-assisted Wi-Fi handoff and automate the collection/download/upload steps around it.

For teacher-owned or already-provisioned phones, device-owner provisioning is likely too intrusive because fully managed device-owner setup is designed for organization-owned devices and normally requires provisioning while the device is unprovisioned. A different transport or a user-assisted handoff is therefore likely more practical unless ARES deploys dedicated managed phones.

## Build

Open `android/ares-sync` as a project in Android Studio and build the `app` module. The current diagnostic builds use JDK 17 and compile against Android API 36.

## Distribution caveat

The low target-SDK builds were ARES-controlled compatibility experiments and do not satisfy current Google Play target-SDK requirements. They are not intended as Play Store release configurations.

## Security

- No Wi-Fi passwords, API credentials, OAuth tokens, or school-private data belong in this repository.
- `ARES2` is currently an open local network, so no Wi-Fi credential is embedded in the app.
- Cleartext HTTP is permitted only for the local hostname `ares.local`; future central upload traffic must use HTTPS.
