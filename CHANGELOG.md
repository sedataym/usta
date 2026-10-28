# Changelog

## Unreleased

- Package the application as `usta`, including OCR models and translation catalogs.
- Consolidate dependency/version declarations and optional Paddle support.
- Preserve legacy settings/presets while migrating to atomic, versioned JSON.
- Separate tab widgets, window lifecycle, settings presentation and capture controllers.
- Own capture and translation jobs explicitly and invalidate stale results after stop/configuration changes.
- Bound IPC queues and isolate temporary capture files per session.
- Add regression tests, packaging checks, style/type checks and contributor documentation.

Linux KDE/GNOME and macOS native behavior remain required release acceptance checks; see `docs/compatibility.md` for actual verification status.
