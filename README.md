# ARES Central Phone Setup Portal

This package implements the centrally hosted Android setup workflow for ARES usage-data collection.

## Included

- Mobile-first school selection and guided setup site.
- School-specific setup URLs and JSON configuration.
- Download links for Round Sync, its exported configuration, and school MacroDroid automation.
- Permission checklist and persistent setup progress stored locally in the browser.
- Internet test-file generator and lightweight setup-event logging.
- Administrator readiness page.
- School configuration generator.
- Local ARES report endpoint, schedule file, and export wrapper.
- Central OneDrive incoming-file processor.
- Deployment, master-phone, release, and testing documentation.

## Not included yet

Two artifacts must be exported from a fully tested Android master phone:

1. `ARES-RoundSync-Config.zip`
2. `ARES-<SCHOOL_CODE>-Automation.macro`

The package deliberately does not fabricate these proprietary app exports.

## Validate

```bash
python3 tools/validate_portal.py
python3 tests/test_portal.py
```

## Preview locally

From the package root:

```bash
php -S 127.0.0.1:8080 -t public
```

Open `http://127.0.0.1:8080/`.
