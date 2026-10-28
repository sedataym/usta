# Compatibility record

The cleanup preserves the existing Linux KDE/GNOME capture paths and macOS Cocoa window behavior. No new Windows support is claimed.

| Environment | Automated contracts | Native acceptance |
| --- | --- | --- |
| macOS / Python 3.14 (local environment) | Passed during each phase; final results in execution ledger | Passed outside sandbox: native fullscreen Space/overlay/focus restoration, shortcut lifecycle and Apple Vision recognition (23 Oct 2026) |
| KDE Wayland with xcb | Portable contracts | Requires real Linux desktop; unverified |
| GNOME Wayland with xcb | Portable contracts | Requires real Linux desktop; unverified |

Manual acceptance: launch; select OCR and translator; select/cancel region; test multiple screens and DPI lock; start/stop/restart; use both shortcuts; restore temporary region after 10 seconds; save/reload presets; restart settings; listen to IPC. On macOS also test another application's native fullscreen Space, focus restoration and Retina. On Linux test Portal allow/deny/cancel and KDE Spectacle fallback. Record OS, CPU architecture, Python/Qt/native tool versions and results before a release.

CI definitions include Python 3.10/3.14 on Linux and macOS, but these remote jobs have not been run during the local cleanup. Python 3.10 is the language/API floor; dependency wheel availability must be verified by that matrix. Multi-monitor/Retina hardware combinations beyond this local host still need manual acceptance.
