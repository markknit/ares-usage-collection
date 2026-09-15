# ARES Sync rc13 field test

Version: `0.8.0-rc13` / versionCode `21`

Purpose of rc13:

- During first-time direct local-network setup, explicitly try both exact school SSIDs: `ARES` and `ARES2`.
- Treat setup as successful when at least one of the two networks can reach `http://ares.local`; when both are available, attempt and verify both.
- Remember the first successful SSID so later due-collection requests try that exact SSID first before falling back to the other exact SSID.
- Keep exact-SSID `WifiNetworkSpecifier` requests rather than an SSID pattern so Android can retain approval for a particular access point when supported.
- Apply the selected ARES app appearance to the Wi-Fi setup helper so progress and failure text remains readable in dark mode.
- Auto-format an eight-character enrollment code as `XXXX-XXXX`; teachers do not need to type the hyphen.

Field checks:

1. With both `ARES` and `ARES2` active, confirm setup visibly checks both and returns success automatically.
2. With only `ARES` active, confirm setup still succeeds after checking `ARES2` rather than ending with an ARES2-not-found failure.
3. With only `ARES2` active, confirm setup succeeds.
4. Repeat with Android/system dark mode and confirm all setup progress and error text is readable.
5. Enter an eight-character enrollment code without a hyphen and confirm the app inserts the hyphen after the fourth character.
6. Keep a normal internet-capable Wi-Fi saved during the tests.

Unresolved until field-tested: whether repeat exact-SSID requests on the same access point skip Android approval, and whether moving to another mesh BSSID requires another approval.
