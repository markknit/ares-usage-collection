# Lesson3 JSON Corpus: Build and Field Installation

## What is stored in GitHub

The canonical curriculum source is the JSON corpus in:

`markknit/cbe-generation-system/data/outputs/v2/`

Do not publish or distribute a prebuilt PostgreSQL database. A database copy would contain
installation-specific secrets and internal identifiers and would be coupled to one database and
migration state. The offline builder instead pins an approved Git commit, validates its JSON,
records checksums, and packages the exact files for Lesson3's supported import interface.

This builder revision pins corpus commit:

`e07c243da77ad4554a2f404ae7790ef6e9d3e1b0`

Expected content:

- 95 lesson-plan JSON files
- 806 lessons
- 7 subjects
- 8 subject-grade combinations

## Build the field package

On an Internet-connected AMD64 Linux machine with Docker Engine and Docker Compose v2:

```bash
sudo bash build_offline_bundle.sh \
  --source "/home/ares/Downloads/ARES_Q4_Update" \
  --output "/home/ares/Downloads/ARES_Q4_Update_offline"
```

The builder downloads the exact pinned corpus commit. It refuses to build if the file count,
lesson count, schema version, per-file size, filename uniqueness, or
`(subject, grade, META.substrand_id)` identity uniqueness differs from the approved values. The
finished field ZIP contains the corpus manifest and checksums.

## Install Lesson3 and the corpus at a school

Run the normal offline installation first:

```bash
cd ARES_Q4_Offline_v0.93_amd64_v1.10
sudo bash preflight.sh ARES-S00XX
sudo bash install_offline.sh ARES-S00XX
```

The installer pauses at the required content step:

1. Open `http://ares.local:3001/login` and create the first Site Administrator.
2. Return to the still-running installer and type `READY`.
3. Enter the Site Administrator email and password when prompted.

The password is not printed or written to the installation receipt. Do not open a second installer
terminal or run the corpus script separately during the normal v1.10 installation.

The corpus installer:

1. verifies the packaged checksums and pinned commit;
2. refuses to run unless Lesson3 has zero plans, versions, subjects, and subject grades;
3. authenticates the Site Administrator;
4. creates a local PostgreSQL rollback snapshot;
5. creates the required taxonomy;
6. imports the 95 JSON files as batches of 50 and 45;
7. verifies 95 plans, 95 Official versions, 806 lesson rows, 7 subjects, and 8 subject grades.

Before importing, the guided installer queries the database and classifies it as `empty`,
`installed`, or `partial`. It imports only an empty database, accepts an already-correct corpus on a
safe rerun, and stops for technical review if partial or unexpected content exists.

If either upload batch or final verification fails, the script stops Lesson3, restores the
pre-import snapshot, restarts Lesson3, and preserves the Site Administrator account. The retained
snapshot path and successful installation details are printed at the end.

For recovery or diagnosis, a technician may query the packaged script directly:

```bash
sudo bash lesson3/corpus/install_lesson3_corpus.sh --status
```

Manual import with `sudo bash lesson3/corpus/install_lesson3_corpus.sh` is reserved for a reviewed
recovery workflow; the normal v1.10 path is the single `install_offline.sh` command.

## Field acceptance check

After the script reports success, sign in and confirm:

- the Lesson Plans list contains 95 plans;
- a sample plan opens for every subject;
- imported plans show Official version `1.0.0`;
- the Site Administrator can still sign out and sign back in;
- the server remains usable after one reboot.

The database counts and automated rollback are strong installation checks, but they do not replace
this human content review on the first disposable/pilot server.

## Updating the corpus later

For a future rollout package:

1. update and review the JSON files in `markknit/cbe-generation-system`;
2. run that repository's Lesson3 validation checks;
3. approve an exact Git commit;
4. update the pinned commit and expected counts in `build_offline_bundle.sh` and
   `templates/install_lesson3_corpus.sh`;
5. build a new numbered offline-builder revision and repeat pilot acceptance.

Do not point the builder at a moving branch such as `main`.

This bootstrap script intentionally does not update a school that already contains lesson plans.
Lesson3 treats a re-import with the same subject, grade, and `META.substrand_id` as a new major
version that is **Not Official** until an administrator reviews and promotes it. Existing-school
corpus updates therefore require a separate reviewed update workflow; they must not be made to look
like a fresh installation.
