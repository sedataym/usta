# Tray and window visibility

Approved in conversation: replace topmost shortcut behavior with main-window visibility toggle, shared with a system tray menu. X hides the main window. Both windows appear above other applications when shown, preserving native macOS fullscreen behavior and Linux window flags. Hiding either window must not stop OCR/translation or hide the other.

Menu: dynamic Hide/Show Main Window, Hide/Show Overlay, Select Region, Select Temporary Region (enabled only while running), separator, Quit. Temporary selection retains its ten-second restore. Quit cleans up listeners, timers, overlay and worker, waiting asynchronously for a running worker.

Approaches: keeping topmost toggling would retain the confusing visible state; duplicating visibility state between menu and hotkey would drift after X. Chosen approach: the control panel owns shared visibility actions; the tray reads real window visibility when opening its menu. Retain serialized hotkey keys for compatibility. Use PySide6 QSystemTrayIcon and existing assets without new dependencies.

Implementation calls: when no system tray is available, X exits normally to avoid an inaccessible background app; log this fallback. Menu updates cannot re-show an explicitly hidden overlay. Normal application startup still shows both windows.

Follow-up: add Start and Stop to the tray, using the existing main-window actions and translated labels. Enable Start only when stopped and Stop only when running; disable both during shutdown.
