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
