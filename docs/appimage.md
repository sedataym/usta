# USTA AppImage Packaging

This document describes the AppImage packaging strategy for USTA without changing the
application source code.

## Strategy

USTA is a Python/PySide6 application with the runtime entry point declared in
`pyproject.toml` as `usta = "src.main:main"`. The AppImage build creates an
AppDir containing:

- the installed USTA Python package,
- Python wheel dependencies from `requirements.txt`,
- the application icon from `src/ui/assets/usta.png`,
- a desktop entry from `packaging/appimage/usta.desktop`,
- an `AppRun` wrapper from `packaging/appimage/AppRun`.

The wrapper starts the app with `python3 -m src.main` and sets `QT_QPA_PLATFORM=xcb`
unless the user already provided a different value.

## Why some dependencies remain system dependencies

USTA integrates with desktop services and external tools that are intentionally not
fully bundled by default:

- `xdg-desktop-portal`, portal backend, session DBus, PipeWire, and GStreamer are
  host desktop services used by portal screen capture.
- `tesseract` and Tesseract language data are host OCR binaries/data used by the
  Tesseract OCR engine.
- `spectacle` is used by the KDE screenshot engine.
- `slurp` is used by the Wayland region selection backend.

Bundling these components inside the AppImage is possible in some cases, but it is
fragile because portal, DBus, compositor, PipeWire, and GStreamer behavior depends on
the running desktop session. The recommended AppImage therefore bundles Python-level
dependencies and documents native desktop requirements.

## Build prerequisites

Install build tools on the host:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install -r requirements.txt
```

The build script uses the project virtual environment at `.venv` by default and does
not install packages with the system Python. Override the interpreter only with a
virtualenv Python if needed:

```bash
PYTHON_BIN=/path/to/venv/bin/python ./scripts/build-appimage.sh
```

The build script automatically downloads `appimagetool` to `build/appimage` when it
is not available in `PATH`.

If you want to provide your own `appimagetool`, pass it explicitly:

```bash
APPIMAGETOOL=/path/to/appimagetool-x86_64.AppImage ./scripts/build-appimage.sh
```

To disable automatic download and fail when `appimagetool` is missing:

```bash
DOWNLOAD_APPIMAGETOOL=0 ./scripts/build-appimage.sh
```

## Build

From the project root:

```bash
./scripts/build-appimage.sh
```

The output is written to `dist/USTA-<version>-<arch>.AppImage`.

Useful environment variables:

- `APP_VERSION`: override the version embedded in the output filename.
- `VENV_DIR`: choose the virtual environment directory; defaults to `.venv`.
- `PYTHON_BIN`: choose the virtualenv Python used for packaging; defaults to
  `.venv/bin/python`.
- `APPIMAGETOOL`: path to the `appimagetool` executable or AppImage.
- `DOWNLOAD_APPIMAGETOOL`: set to `0` to disable automatic `appimagetool` download.
- `BUILD_DIR`, `APPDIR`, `DIST_DIR`: override build and output locations.
- `ARCH`: override the AppImage architecture passed to `appimagetool`.

## Runtime dependencies by feature

### Common desktop capture stack

Install these on systems where portal capture is used:

- `xdg-desktop-portal`
- one matching portal backend such as `xdg-desktop-portal-kde` or
  `xdg-desktop-portal-gnome`
- `pipewire`
- GStreamer base/good plugins and PipeWire plugin
- PyGObject/GI bindings if portal capture is selected by the installed runtime path

### OCR

- RapidOCR/ONNXRuntime is installed as a Python dependency.
- Tesseract mode requires the host `tesseract` executable and language data packages.
- EasyOCR is listed in `requirements.txt` and can make the AppImage significantly
  larger because it may pull heavy ML dependencies.
- PaddleOCR is optional in the codebase and is not enabled by default in
  `requirements.txt`.

### Screenshot and region selection tools

- KDE screenshot mode requires `spectacle`.
- Slurp region selection requires `slurp`.

## Validation checklist

After building, run:

```bash
chmod +x dist/USTA-*.AppImage
./dist/USTA-*.AppImage
```

Validate the following:

- The USTA control panel opens and displays the application icon.
- Settings are persisted under the platform configuration directory.
- RapidOCR can be selected and initialized.
- Tesseract mode works when `tesseract` and language packs are installed; otherwise
  the failure is visible and understandable.
- KDE screenshot mode works when `spectacle` is installed.
- Portal screenshot mode works with the matching desktop portal backend, PipeWire,
  and GStreamer plugins installed.
- Region selection works when the chosen sniper backend dependencies are installed.

## Notes

This build path avoids changes to application modules such as `src/main.py` and keeps
all AppImage-specific behavior in `packaging/appimage` and `scripts`.
