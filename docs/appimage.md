# USTA AppImage Packaging

This document describes the AppImage packaging strategy for USTA without changing the
application source code.

## Strategy

USTA is a Python/PySide6 application with the runtime entry point declared in
pyproject.toml as `usta = "src.main:main"`. The AppImage build creates an
AppDir containing:

- the Python executable used for the build,
- the matching libpython*.so* shared library files,
- the matching Python standard library under `usr/lib/pythonX.Y`, including
  native runtime modules such as `lib-dynload`,
- the installed USTA Python package,
- Python wheel dependencies from requirements.txt,
- the application icon from src/ui/assets/usta.png,
- a desktop entry from packaging/appimage/usta.desktop,
- an `AppRun` wrapper from packaging/appimage/AppRun,
- available GLib/GObject/GStreamer GI typelibs and plugins needed by portal
  screenshot capture.

The wrapper starts the app with python3 -m src.main, points PYTHONHOME at the
bundled usr runtime, limits PYTHONPATH to bundled application paths, disables
user site-packages with PYTHONNOUSERSITE=1, and sets QT_QPA_PLATFORM=xcb
unless the user already provided a different value. It also points GI_TYPELIB_PATH,
GST_PLUGIN_PATH, GST_PLUGIN_SYSTEM_PATH, and GIO_MODULE_DIR at bundled runtime
directories when they exist.

This makes the AppImage independent of the host Python installation for normal
Python startup. For example, an AppImage built with Python 3.14 bundles the
Python 3.14 executable, libpython3.14.so*, standard library, and Python native
extension modules so it can start on a system that only has Python 3.12 installed.

## Why some dependencies remain system dependencies

USTA integrates with desktop services and external tools that are intentionally not
fully bundled by default:

- xdg-desktop-portal, portal backend, session DBus, PipeWire, and GStreamer are
  host desktop services used by portal screen capture.
- tesseract and Tesseract language data are host OCR binaries/data used by the
  Tesseract OCR engine.
- spectacle is used by the KDE screenshot engine.
- slurp is used by the Wayland region selection backend.

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

The build script uses the project virtual environment at .venv by default and does
not install packages with the system Python. Override the interpreter only with a
virtualenv Python if needed:

```bash
PYTHON_BIN=/path/to/venv/bin/python ./scripts/build-appimage.sh
```

The build script automatically downloads appimagetool to `build/appimage` when it
is not available in `PATH`.

The virtual environment Python determines the bundled runtime version. If the
release should run as a Python 3.14 AppImage, create the virtual environment with
Python 3.14 before installing dependencies:

```bash
python3.14 -m venv .venv
.venv/bin/python -m pip install --upgrade pip setuptools wheel
.venv/bin/python -m pip install -r requirements.txt
```

The build fails early if it cannot locate the matching Python standard library or
libpython*.so*, because otherwise the AppImage would still depend on the same
Python runtime being installed on the target machine.

If you want to provide your own appimagetool, pass it explicitly:

```bash
APPIMAGETOOL=/path/to/appimagetool-x86_64.AppImage ./scripts/build-appimage.sh
```

To disable automatic download and fail when appimagetool is missing:

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
- `VENV_DIR`: choose the virtual environment directory; defaults to .venv.
- `PYTHON_BIN`: choose the virtualenv Python used for packaging; defaults to
  `.venv/bin/python`.
- `APPIMAGETOOL`: path to the appimagetool executable or AppImage.
- `DOWNLOAD_APPIMAGETOOL`: set to `0` to disable automatic appimagetool download.
- `BUILD_DIR`, `APPDIR`, `DIST_DIR`: override build and output locations.
- `ARCH`: override the AppImage architecture passed to appimagetool.

## Bundled Python runtime

The AppImage build copies the runtime pieces required for Python startup:

- usr/bin/python3: the real Python executable from the selected virtual
  environment.
- `usr/lib/libpython*.so*`: the shared Python library detected from ldd and
  Python sysconfig metadata, with expected soname symlinks created when needed.
- `usr/lib/pythonX.Y`: the matching standard library and platform native runtime
  modules when they are separate from the base standard library.
- usr/lib/pythonX.Y/lib-dynload: native Python extension modules required by
  standard-library modules such as ssl, ctypes, and compression modules.
- `usr/app/site-packages`: application and wheel dependencies installed by `pip`.
- selected native shared libraries required by bundled Python modules and wheel
  extensions, such as compression libraries used by EasyOCR/PyTorch stacks.

During the build, the script validates the bundled interpreter by importing
encodings, ctypes, ssl, and the USTA entry module. This catches missing
stdlib or `libpython` issues before the AppImage is produced.

## Runtime dependencies by feature

The bundled Python runtime removes the requirement for the target system to have
the same Python version installed. It does not remove native desktop integration
requirements or compatibility constraints from the Linux base system.

The following remain host/runtime environment dependencies:

- a compatible glibc and core Linux userspace for the binaries used during build,
- graphics/session libraries used by Qt, X11, Wayland, and desktop integration,
- portal, host PipeWire session services, OCR tools, and region-selection utilities
  listed below.

### Common desktop capture stack

Install these on systems where portal capture is used:

- xdg-desktop-portal
- one matching portal backend such as `xdg-desktop-portal-kde` or
  `xdg-desktop-portal-gnome`
- `pipewire`
- GStreamer base/good plugins, PipeWire plugin, and GLib/GObject GI typelibs on
  the build machine, so the AppImage can copy the required typelibs and plugins
  into the bundle

The AppImage build copies available GLib, GObject, GModule, Gio, GIRepository,
Gst, GstBase, and GstVideo typelibs plus the app, PipeWire, and video conversion
plugins into the AppDir. Portal capture still depends on the running desktop's
xdg-desktop-portal backend and PipeWire session.
If the bundled GI/GStreamer runtime cannot be loaded, the application logs the
portal unavailability reason and shows an alert. It does not switch to the KDE
Spectacle screenshot engine automatically; the user can choose Spectacle from the
alert or from the screenshot engine selector.

### OCR

- RapidOCR/ONNXRuntime is installed as a Python dependency.
- Tesseract mode requires the host tesseract executable and language data packages.
- EasyOCR is listed in requirements.txt and can make the AppImage significantly
  larger because it may pull heavy ML dependencies.
- PaddleOCR is optional in the codebase and is not enabled by default in
  requirements.txt.

### Screenshot and region selection tools

- KDE screenshot mode requires spectacle.
- Slurp region selection requires slurp.

## Validation checklist

After building, run:

```bash
chmod +x dist/USTA-*.AppImage
./dist/USTA-*.AppImage
```

To specifically validate Python runtime independence, run the AppImage on a
system or container where Python 3.14 is not installed, for example a Python 3.12
desktop environment. Confirm that the process no longer fails with a missing
libpython3.14.so or missing encodings/stdlib error before the UI appears.

Validate the following:

- The USTA control panel opens and displays the application icon.
- Settings are persisted under the platform configuration directory.
- RapidOCR can be selected and initialized.
- Tesseract mode works when tesseract and language packs are installed; otherwise
  the failure is visible and understandable.
- KDE screenshot mode works when spectacle is installed.
- Portal screenshot mode works with the matching desktop portal backend, PipeWire,
  and bundled or host-compatible GStreamer plugins available.
- Region selection works when the chosen sniper backend dependencies are installed.

To validate the GStreamer GI namespace from the AppImage runtime without opening
the UI, extract or mount the AppImage and run its AppRun environment with:

```bash
./dist/USTA-*.AppImage --appimage-extract
APPDIR="$PWD/squashfs-root" "$PWD/squashfs-root/AppRun" --help
```

During build, the script also attempts to import Gst from the bundled Python
runtime and prints whether the bundled GStreamer GI runtime is available.

## Notes

This build path avoids changes to application modules such as `src/main.py` and keeps
all AppImage-specific behavior in `packaging/appimage` and `scripts`.
