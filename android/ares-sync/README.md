# ARES Sync Android MVP

ARES Sync is the replacement for the Automate/legacy-extension phone workflow.

## MVP goal

Prove on the pilot Android phone that a normal Android application can:

1. request the local-only `ARES2` Wi-Fi network with supported Android APIs;
2. reach `http://ares.local/` over the network returned to the application;
3. download the due usage CSV into app-private storage; and
4. repeat the same specific network request without editing a flow or using deprecated Android Wi-Fi APIs.

The MVP intentionally does not yet include scheduling, central HTTPS upload, enrollment, or the final guided setup portal.

## Build

Open `android/ares-sync` as a project in Android Studio and build the `app` module.

The project targets Android API 36, requires Android 10 (API 29) or newer, and uses JDK 17 source compatibility.

## Security

- No Wi-Fi passwords, API credentials, OAuth tokens, or school-private data belong in this repository.
- Cleartext HTTP is permitted only for the local hostname `ares.local`; future central upload traffic must use HTTPS.
