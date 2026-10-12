# Lesson3 v0.94 Offline Acceptance Checklist

Use this checklist on one clean, disposable Ubuntu 24.04 ARES server before approving the v1.11
field package for rollout. Keep the validated v1.10 package unchanged as the fallback until every
required check below passes.

## Required evidence

Record the field ZIP filename and SHA-256, school code, test date, tester, target hostname, and the
installation log path. Do not record administrator or teacher passwords.

## 1. Offline installation

1. Disconnect the target server from the Internet.
2. Extract `ARES_Q4_Offline_v0.94_amd64_v1.11.zip`.
3. Run `sudo bash preflight.sh ARES-S00XX` and require `0 failures`.
4. Run `sudo bash install_offline.sh ARES-S00XX`.
5. Create the first Site Administrator when prompted and complete the guided corpus import.
6. Require the final installer success message and the verified counts of 95 lesson plans and 806
   lessons.
7. Confirm the deployed release file contains exactly `v0.94`:

   ```bash
   cat /mnt/sda3/var/www/lesson3-download/lesson3-deploy/VERSION
   ```

8. Reboot the server while it remains offline. Confirm `http://ares.local:3001/login` opens and
   sample plans from at least three subjects still show Official version `1.0.0`.

## 2. Teacher discussions

Create two disposable, verified teacher accounts. Use separate browser profiles or devices so the
two sessions remain independent.

1. Sign in as Teacher A and confirm **Discuss** is visible without changing a feature setting.
2. Start a topic without a lesson reference. Confirm Teacher B can read and reply.
3. Confirm Teacher A receives the blue unread indication after Teacher B replies, and that opening
   the thread clears the indication for the displayed posts.
4. Start another topic using **Share -> Discuss this version** from a lesson page. Confirm the topic
   opens the exact referenced version and **Compare changes** works when applicable.
5. Search for a word in the topic title and confirm the topic is found. Search for a word present
   only in the post body and confirm it is not found; v0.94 search is title-only.

## 3. Administrator controls

1. As the Site Administrator, pin and unpin a test topic.
2. Redact one test reply and confirm its original text is no longer visible in the live application.
3. Delete a separate test thread and confirm the entire thread and its replies disappear.
4. Open **Manage -> System -> Features**, disable Discussions, confirm with the administrator
   password, and verify a teacher no longer sees Discuss or its entry points.
5. Follow **Moderate discussions** while the feature is disabled and confirm retained discussions
   remain available to the Site Administrator for moderation.
6. Re-enable Discussions and confirm the retained test topic becomes visible again.

Redaction and deletion are destructive. Use only disposable test content. Existing database backups
can retain earlier text until those backups expire.

## 4. Regression checks

- Open and download a lesson as PDF and Word.
- Save an edited version, compare it with the Official version, and promote it only if using
  disposable test content.
- Confirm the local Lesson3 User Guide opens from
  `http://ares.local/modules/Lesson_Plans/LESSON3_USER_GUIDE.pdf`.
- Confirm `http://ares.local/app_install/` and the APK download still work.
- Confirm ARES usage collection, school-code reassignment, `ares.local`, and tracking checks remain
  successful.
- Confirm Tailscale and TigerVNC remain stopped, disabled, and unregistered, and `x11vnc` remains
  disabled.

## 5. Optional ZIP-import check

The normal v1.11 installer deliberately retains the proven two-batch JSON corpus import. To test the
new v0.94 administrator ZIP upload without changing content, create a ZIP containing copies of
already-installed corpus JSON files and upload it under **Manage -> Lesson plans**. Require the
report to classify unchanged files as skipped and to create no additional plans or lessons.

Use Lesson3 directly on port 3001 for this test. If a future deployment instead sends large ZIP
uploads through an Nginx reverse proxy, configure at least `client_max_body_size 201m` and
`proxy_read_timeout 300s` before testing that proxy path.

## Approval rule

Approve v1.11 for rollout only when every required check passes and the recorded evidence is
reviewed. A successful connected build alone is not acceptance. If any v0.94 check fails, retain
v1.10/v0.93 for rollout while the failure is investigated.
