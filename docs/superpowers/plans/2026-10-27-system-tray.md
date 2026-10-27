# System Tray Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Add tray actions and a shared main-window visibility shortcut on Linux and macOS.

**Architecture:** ControlPanel owns visibility and graceful exit. A small SystemTray component builds and refreshes the menu. The overlay emits a stateless toggle request, preserving shortcut configuration compatibility.

**Tech Stack:** Python, PySide6, gettext, unittest.

**Spec:** docs/superpowers/specs/2026-10-27-system-tray-design.md

## Global Constraints

- Preserve native macOS fullscreen panels and Linux overlay flags.
- Hidden windows must not interrupt OCR/translation.
- Retain saved hotkey configuration keys.
- No new dependencies.

## Review Focus

- X and hotkey interaction must use actual visibility.
- Hidden overlay must stay hidden on translation updates.
- Running-worker exit must wait for worker completion.
- Missing tray must not strand the application.
- Temporary selection must be disabled when stopped or already selecting.

### Task 1: Tray, shared visibility and graceful exit

**Files:** Create src/usta/ui/system_tray.py; modify src/usta/ui/main_window.py, overlay_window.py, main.py; tests/integration/test_control_panel.py and platform window tests.

**Interfaces:** ControlPanel.toggle_main_window(), toggle_overlay(), show_main_window(), hide_main_window(), request_quit(); SystemTray.refresh(), available.

- [x] Write regression tests for menu/shortcut/X sequences, independent overlay visibility, missing-tray exit, and asynchronous worker shutdown.
- [x] Run tests and confirm failure against the current implementation.
- [x] Add tray component and route hotkey through the shared action. Preserve native presentation and always-on-top flags. Separate close-to-tray from explicit shutdown.
- [x] Run integration tests and update existing native window tests for the new contract.

### Task 2: Copy, translations and verification

**Files:** Hotkeys tab, Turkish/Ukrainian gettext catalogs, README.

- [x] Rename the user-facing shortcut and describe tray usage/fallback.
- [x] Compile catalogs using Babel.
- [x] Run full unittest suite, Ruff checks and mypy; review final diff for shutdown/visibility races.

## Execution notes

User explicitly requested implementation in the existing project; execute inline in the clean feature/macos_support_1 checkout. No new worktree or commits requested. Baseline and verification outputs are saved under /tmp/usta-tray-*.log.


## Verification and review

- Baseline: 105 tests; three Unix-socket permission errors inside sandbox, 29 platform skips. Socket tests pass outside sandbox.
- Final portable suite: 113 tests, OK, 29 platform skips (`QT_QPA_PLATFORM=offscreen`).
- Native macOS window suite: 21 tests, OK, including fullscreen/focus and show/hide behavior.
- Ruff lint/format, mypy, pip dependency check and git diff whitespace check pass.
- Wheel and sdist rebuilt successfully. The initial artifact mismatch was caused by old dist catalogs after translation updates; the rebuilt package passes resource checks.
- Read-only independent review found one delayed temporary-selection race. Regression test reproduced it; entry point now rechecks worker state, and integration tests pass.
- Running all tests on the native desktop stalled in the existing modal color-dialog integration test; that run was stopped. Integration tests pass offscreen, and native-specific tests pass separately on the real desktop.
- Linux window contracts pass using the Linux code path on this macOS host; a live Linux desktop was not available.
