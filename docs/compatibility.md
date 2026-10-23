# Compatibility record

The cleanup preserves the existing Linux KDE/GNOME capture paths and macOS Cocoa window behavior. No new Windows support is claimed.

| Environment | Automated contracts | Native acceptance |
| --- | --- | --- |
| macOS / Python 3.14 (local environment) | Run during each phase | Baseline sandbox cannot access WindowServer/Vision recognition; unverified |
| KDE Wayland with xcb | Portable contracts | Requires real Linux desktop; unverified |
| GNOME Wayland with xcb | Portable contracts | Requires real Linux desktop; unverified |

Manual acceptance: launch; select OCR and translator; select/cancel region; test multiple screens and DPI lock; start/stop/restart; use both shortcuts; restore temporary region after 10 seconds; save/reload presets; restart settings; listen to IPC. On macOS also test another application's native fullscreen Space, focus restoration and Retina. On Linux test Portal allow/deny/cancel and KDE Spectacle fallback. Record OS, CPU architecture, Python/Qt/native tool versions and results before a release.
