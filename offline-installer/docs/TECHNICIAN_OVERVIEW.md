# ARES v1.13 - Technician Overview

Offline school installation | Lesson Plan Editor v0.94 | Local server address: ares.local

## Purpose and requirements

This package adds the current ARES modules to an approved Ubuntu 24.04 AMD64
ARES base system. It is not an operating-system image and does not contain the
whole school content library. Restore the approved ARES base image first.

Bring the complete verified installer ZIP, the school's assigned ARES-S00XX
code, administrator access and an Android phone for the final collection check.
Phone enrollment uses a separate one-time key supplied by ARES staff.
Keep the ZIP and this overview on a separate Windows computer or external drive.

## Included components

- **Lesson Plans:** the local lesson-plan directory, PDF material and Lesson3 user guide.
- **Lesson Plan Editor:** Lesson3 v0.94, its database and PDF-export service, loaded from bundled Docker images. The supplied corpus has 95 lesson plans and 806 lessons.
- **ARES Sync:** server usage-export and tracking support, approved Android APK and the local phone installation page.
- **Admin tools:** the approved admin page, Admin_tools module entry and ARES Sync user guide, installed as one content update. The admin folder keeps its existing password protection.
- **Tsavo Trust:** the module page, logo, six offline videos and tracking mapping.
- **Local addressing:** ares.local alongside the school hostname (for example tsavo3.local). Publication starts automatically when a LAN address is available.
- **AnyDesk:** reset the cloned identity once per school server, set the unattended password and save its new ID. Same-school reinstalls retain it. Use a base image captured before school personalization.
- **Optional support:** password-protected VNC over the school LAN without Internet, plus Tailscale browser SSH/VNC for off-site support. Activation is a separate choice; only Tailscale enrollment needs Internet.
- **Internet Lockdown v1.4.2:** the supplied tools and operating manual. Setup does not apply firewall rules or enable reboot lockdown. Existing active lockdown is preserved.

The server installation needs no Internet downloads. Central phone enrollment
and later uploads still need normal Internet or mobile data on the phone.

<!-- pagebreak -->

## Installation process

1. **Prepare the server.** Start from the approved ARES base image. Connect the
   school LAN and keep a working local console or support connection available.
2. **Extract the whole ZIP into a new folder.** Open a normal Ubuntu terminal in
   that folder. Run the master command, replacing the example with the real code:

   ```bash
   sudo bash install_offline.sh ARES-S00XX
   ```

3. **Follow Lesson3 setup.** When prompted, open http://ares.local:3001/login,
   create the first Site Administrator and store its credentials privately.
   Return to the terminal, type READY and supply the administrator details when
   asked. The installer imports and checks the corpus. An already installed
   corpus is recognized rather than imported again.
4. **Choose optional support.** For headless/on-site support, activate the LAN
   desktop and set the VNC password. Decline the later Tailscale prompt if offline;
   the LAN desktop remains active. AnyDesk setup asks for RESET and a hidden
   password; use a local console because reset disconnects AnyDesk sessions. Save
   the new ID, or retrieve it later if Pending. Lockdown commands install without
   an adapter; first use selects the student LAN. Do not select a modem-only uplink.
   Existing active or boot-enabled lockdown may defer optional setup.
5. **Read the final result.** Require the core installation success message and
   keep the installation log path. Optional-tool warnings do not cancel core
   success. Stop and send the printed log to ARES support if a core step fails.

The master performs package checks automatically. Technicians do not need to
run separate checksum or build-qualification commands at every school.

## Check before leaving

- From another device on the school LAN, open http://ares.local/. Check the
  Lesson Plans and Tsavo Trust entries; play the videos and try seeking.
- Sign in at http://ares.local:3001/login, open a plan and export a PDF.
- Open http://ares.local/app_install/index.html. Download the APK, then complete
  ARES Sync enrollment with the one-time key and check school discovery/collection.
  Keep one-time enrollment keys private.
- Open the protected Admin Tools page and its ARES Sync user-guide link.
- Confirm the support connections the school uses still work. Remote preparation
  preserves existing support services. For LAN-only activation, run
  `sudo ares-enable-remote-access --lan-only`. Connect the technician computer
  to the school LAN, open `<SERVER-LAN-IP>::5901` in the VNC viewer and enter
  the VNC password. No Internet or Tailscale is required. For off-site support,
  activate Tailscale, keep its app connected on the support computer and save the
  school's Tailscale address in the VNC viewer, port 5901. Open the saved connection
  and enter the VNC password. No PowerShell tunnel is needed. Browser SSH is
  available through the Tailscale admin console when permitted by its policy.
  Browser SSH alone does not connect the Windows Tailscale app.

Before reloading a test server, follow docs/PRE_RELOAD_PRESERVATION.md. Keep the
Clonezilla base image, final installer ZIP and backups off the disk being erased.
