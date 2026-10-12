ARES Sync Rollout Package
Prepared: 2026-10-11
Repository branch: production-baseline-cleanup
Builder release: ARES Q4 Offline Installer v1.11

CONTENTS

guides/
  ARES_Sync_Technician_Guide.pdf
    End-to-end technician procedure: school-server update, school-code
    reassignment, guided Lesson3 corpus installation, dormant remote-access
    preparation, phone installation, enrollment, verification, teacher handoff,
    and troubleshooting.

  ARES_Sync_Teacher_Guide.pdf
    Teacher installation, normal-use, data-use, and support guidance.

server-installer/
  update_school_server.sh
    Recommended technician entry point.

  ares_set_school_code.sh
    Source for the installed school-code reassignment command.

  install_usage_collection.sh
  ares_prepare_usage_upload.sh
  prepare_usage_upload.php
  prepare_due_usage_upload.php
  collection_schedule.json
    Required files used by the update script. Keep these files together.

SCHOOL-SERVER UPDATE WITH A FINAL SCHOOL ID

1. Copy or extract this complete package onto the school server.
2. Open a terminal in the ARES_Sync_Rollout_Package directory.
3. Replace ARES-S00XX with the school's canonical ID and run:

   sudo bash server-installer/update_school_server.sh --school-code ARES-S00XX

4. Do not continue to phone enrollment unless the command reports both:

   ARES usage-collection server installation complete.
   AUTO export smoke test passed

5. Record the backup-directory path and measured CSV byte count.

PROVISIONAL INSTALLATION BEFORE THE FINAL SCHOOL ID IS KNOWN

Use a unique provisional value for each server, for example:

   sudo bash server-installer/update_school_server.sh --school-code PENDING-SRV001

Do not enroll a teacher's phone while the server has a provisional code.
After the canonical school ID is assigned, replace ARES-S00XX and run:

   sudo ares-set-school-code ARES-S00XX

Continue to phone enrollment only after the command reports the new school
code and a verified AUTO export filename beginning with that same final ID.
The command backs up the prior configuration and restores it automatically if
the verification export fails.

If ares-set-school-code is not found, install this current package once with
update_school_server.sh; that installs the reassignment command.

The technician must confirm that the final ID is the one assigned in the
central ARES school registry. The command validates the ID format and local
export behavior; it does not query the central registry.

The server must already have the normal ARES usage tracker, report builder,
and nonempty combined_usage.csv. This package does not install or repair the
base usage-tracking system.

SECURITY

This package contains no APK, passwords, signing keys, enrollment keys,
device credentials, central-service credentials, or private school data.
