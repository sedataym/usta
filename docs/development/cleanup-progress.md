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
