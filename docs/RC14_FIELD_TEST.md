# ARES Sync rc14 field-test note

Version: `0.8.0-rc14` / versionCode `22`

rc13 field result:

- PASS: setup worked with only one ARES network available.
- PASS: setup worked with both `ARES` and `ARES2` available.
- PASS: successful setup returned automatically to the main screen and reported completion.
- PASS: dark-mode setup text was readable.
- PASS: enrollment-code hyphen insertion worked.
- MINOR UX ISSUE: after `ARES` had already connected and reached `ares.local`, rc13 still launched a second explicit `ARES2` request. If `ARES2` was absent, Android briefly displayed its generic system message: `Something came up. The application has cancelled the request to choose a device.` The app then completed successfully.

rc14 correction:

- Setup now stops immediately after the first ARES SSID successfully connects and reaches `ares.local`.
- It tries `ARES` first, then falls back to `ARES2` only if `ARES` is unavailable or cannot reach the school server.
- This avoids launching an unnecessary second Android network-selection request after setup has already succeeded, preventing the misleading system cancellation message in the successful-one-network case.
- Both `ARES` and `ARES2` remain registered as Wi-Fi suggestions, and later due-collection logic still remembers the successful SSID and can fall back to the alternate SSID when required.

Because rc13 otherwise passed the requested field checks, rc14 is considered a small UX correction rather than a new connection architecture. A separate rc14 field test is optional before proceeding to the next production milestone, but final production-signed acceptance must still cover the complete setup flow.
