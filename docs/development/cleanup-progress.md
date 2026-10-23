# Cleanup execution ledger

Plan: ../superpowers/plans/2026-10-23-project-cleanup.md

Ruling: Work in the existing feature/macos_support_1 checkout; preserve the existing environment and keep changes reviewable in place. No main branch changes or external publication.
Ruling: Real KDE/GNOME acceptance needs an actual Linux desktop; implement and run portable contracts here, explicitly leave native acceptance unverified.
Pre-flight: Tasks 4/6/7/8 share settings/results/worker interfaces; migrate their consumers in the same task, retaining Qt signals and public launch commands. Task 3 changes all import paths before subsequent modules are introduced.

## Baseline
Host: macOS-26.5.2-arm64-arm-64bit-Mach-O; Python 3.14.7
- PySide6: 6.11.2
- googletrans: 4.0.2
- rapidocr-onnxruntime: 1.2.3
- pynput: 1.8.2
- deepl: 1.32.0

Task 1: portable baseline 33 tests, 21 native skips, 0 failures. Initial unrestricted discovery aborted in Cocoa and Vision recognition failed because desktop services are inaccessible in sandbox (log /tmp/usta-baseline.log). Native tests now explicitly opt in. Linux window contracts run offscreen on either OS.

Task 2: metadata regression failed before fix (missing DeepL). Dependency declarations now have one source and paddle/dev extras. Python 3.10 is the syntax/API floor, NOT a claim that all untested dependency combinations support 3.10; local 3.14 is recorded separately. Full lower-version install matrix remains CI validation. Existing environment pip check passed.

Task 3: package layout tests failed before move and pass after; 36 portable tests green (21 skips); editable install succeeded. Resources resolve through importlib.resources with process-owned extraction lifetime. Wheel/sdist inspection follows once build tool installation completes. Model bytes unchanged by directory moves.

Task 3 artifact follow-up: wheel and sdist built; all resources present in both.
Task 4: six storage regression tests passed; full portable suite 42 tests green (21 skips). Primitive-only legacy migration preserves originals, future/corrupt JSON cannot be overwritten, atomic replace failure preserves last settings. UI load signals blocked and does not save.

Task 5: import side-effect test reproduced stdout output before removal and passes after. 43 portable tests green (21 skips); config no longer creates directories; bootstrap owns path preparation and logging. Diagnostic print calls replaced with module loggers; OCR content/key diagnostics are debug-only.

Task 6: three new engine contract tests plus full suite pass (46 tests, 21 skips). Managers lazily construct selected engines; provider failures use EngineError and existing read_text string boundary is retained for backend compatibility, with typed read_result/translate_request boundaries for pipeline. Ruling: installed RapidOCR 1.2.x has no public thread-count option (source inspected); preserve proven patch in dedicated adapter rather than changing runtime threading.

Task 7: Event-controlled delayed API, reconfiguration and EngineError tests pass; full portable suite 50 tests (21 skips). Capture/engine state owned by the loop; immutable jobs and session invalidation suppress stale results. GUI stop is non-blocking, close waits via finished signal. Portal sessions survive region changes; native command waits bounded. Ruling: DeepL SDK constructor has no timeout/retry keyword parameters; contract regression caught this and implementation retains SDK's finite built-in timeout/backoff policy (source inspected), rather than global monkey-patching.

Task 8: architecture tests failed on core→UI imports and panel mutation, pass after split. Tabs own widgets and emit actions; application/region/hotkey controllers and settings presenter separate responsibilities. Linux/macOS window algorithms retained in UI platform modules. Two real Qt offscreen integration tests confirm load does not save, user change saves once, preset cancels temporary restore. Full suite validation recorded below.

Task 9: private capture workspace and real Unix socket tests pass outside sandbox (sandbox forbids bind). Full suite 58 tests green, 21 native skips. Active socket and ordinary files are preserved, pending broadcasts bounded, independent capture workspaces cleaned individually. IPC JSON/address retained. New screenshot factory avoids importing Linux native modules on macOS.

Task 10: Ruff check/format and mypy (four boundary modules) pass. Contributor, architecture, testing, compatibility and model provenance docs added; README macOS status corrected. UI status/preset messages now use existing TR/UK catalogs; native callback names and window algorithms retained. Model provenance is explicitly unverified rather than assuming source-code license covers models.

Task 11 implementation: CI matrix and package workflow added; wheel/sdist build and byte-for-byte resource checks passed. Clean no-dependency wheel venv imported package/resources/entry point outside repo; full dependency install is defined in CI, not claimed locally. Native macOS suite passed all 59 tests without skips outside sandbox, including fullscreen host helper and Vision. Final acceptance found queued Qt delivery could outlive stop and repeated start could request restart: both reproduced RED and fixed GREEN with new worker signal tests. RapidOCR compatibility option/idempotence contract added. Real Linux KDE/GNOME, AppImage execution, remote CI and additional Python/architecture combinations remain unverified external checks.

Final acceptance before review: all 63 tests passed with USTA_NATIVE_TESTS=1 (no skips), Ruff check/format passed, mypy passed, pip check passed, Bash syntax checks passed. Clean wheel imported all eight ONNX models and catalogs outside repository. Synthetic Apple Vision comparison on same host/image: baseline median 31.5 ms, current 32.3 ms, six warm samples each; identical recognized text. This small timing difference is not a full OCR/provider performance certification. Remaining external checks: Linux desktop/AppImage, remote CI and extra hardware/interpreter combinations.

## Independent final review and fix pass

A fresh gpt-6-astra reviewer examined the full branch read-only. P1 malformed preset data loss and P2 UI unknown-field loss were confirmed. Two additional findings (overlay state during queued restart and stale installed AppImage version) were regraded Important because they affect supported start/stop behavior and release artifact identification; all four were fixed in this single pass.

Final: fixed malformed-preset overwrite — store/presenter regressions RED→GREEN; valid entries recover and writes remain blocked until malformed original is repaired.
Final: fixed unknown settings fields lost on UI save — Qt regression RED→GREEN; loaded model metadata retained.
Final: fixed overlay mode after queued restart — false/true status replay RED→GREEN.
Final: fixed AppImage version source — metadata regression RED→GREEN; source version file used without GUI import.
No review findings deferred. Linux desktop/AppImage and remote CI remain external acceptance items, not successful checks. Generated native scratch file accidentally included in the CI commit was removed and ignored.

## Final verification

- `USTA_NATIVE_TESTS=1 .venv/bin/python -m unittest discover -s tests -v`: **72 passed, zero skips**, 11.076 seconds, outside sandbox. Includes native fullscreen/overlay/focus, Vision, hotkey lifecycle, real IPC, portable Linux factory/window contracts, storage and review regressions.
- `ruff check .`, `ruff format --check .`: passed.
- `mypy`: passed on four declared boundary modules.
- `python -m pip check`: no broken requirements.
- `python -m build --no-isolation`: wheel and sdist built. All source model/catalog bytes match both artifacts.
- Clean wheel venv outside repository: package/resources/entry point imported. Installed wheel Qt startup/close smoke passed using shared existing runtime dependencies; no user settings touched. This is separate from the full clean dependency install in the unrun CI workflow.
- `bash -n scripts/build-appimage.sh packaging/appimage/AppRun` and `git diff --check`: passed.
- All eleven implementation stages have landed locally. Full Linux desktop/AppImage acceptance, remote CI version matrix, extra monitor/architecture combinations and exhaustive OCR memory/performance benchmarking remain unverified; they are not marked passed.
- Changes retained on existing `feature/macos_support_1`; no merge, remote push, release or publication performed.

## Follow-up: macOS startup warnings

User reported repeated pynput Accessibility warnings and Qt monospace alias lookup. Root causes verified in installed pynput's AXIsProcessTrusted check and StatusTab stylesheet. Missing Accessibility trust is now explained once per denied period; only pynput's duplicate message is filtered, event-tap startup and Linux listener behavior are preserved. StatusTab uses Qt's available system FixedFont. Three regressions added (permission warning deduplication, permission recheck for a new listener, system font). Final native suite: 75 passed, zero skips; Ruff check/format and mypy passed. macOS permissions were not modified by the application.
