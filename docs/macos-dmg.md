# macOS DMG

The current recipe builds USTA for **Apple Silicon (arm64), macOS 26 or newer**.
The Python runtime used for this release has a macOS 26 deployment target.
The application includes Python, PySide6, RapidOCR models, Apple Vision bindings,
and the EasyOCR/PyTorch dependencies. No separate Python installation is needed.

## Build

From an Apple Silicon Mac with the project virtual environment installed:

```sh
.venv/bin/python -m pip install 'pyinstaller>=6.16,<7'
./scripts/build-dmg.sh
```

The script builds and signs `dist/macos/USTA.app`, runs offline diagnostics,
and creates `dist/macos/USTA-<version>-macOS-arm64.dmg` and its SHA-256 checksum.
The disk image contains the application, an Applications shortcut and install notes.
Diagnostics verify Qt/SVG resources, translations, dynamic engine imports,
EasyOCR/PyTorch, macOS-specific entries in the actual OCR tab combo boxes, and
actual RapidOCR/Apple Vision recognition of a generated image.
They do not capture the screen, start keyboard listeners or make network calls.
The report is saved to `build/macos/bundle-check.json`.

PyInstaller's cache and intermediate files stay under `build/macos`.
Set `PYTHON_BIN` to use another compatible project Python environment.

## Signing and installation

Without `USTA_CODESIGN_IDENTITY`, the build uses a local ad-hoc signature. This
verifies bundle integrity but is **not an Apple Developer ID signature or Apple
notarization**. macOS may require approval under System Settings → Privacy &
Security → Open Anyway. Drag USTA.app to Applications before granting its permissions.
Set `USTA_CODESIGN_IDENTITY` to a valid Developer ID identity for a signed build;
notarization remains a separate release step requiring an Apple developer account.

The application needs Screen & System Audio Recording access for capture, and
Accessibility and potentially Input Monitoring access for global shortcuts.
Quit from the tray and relaunch after changing permissions.

RapidOCR and Apple Vision work locally. EasyOCR downloads its models on first use.
Google/DeepL translation needs internet access; DeepL also needs an API key.
Tesseract and its language data are external optional dependencies; PaddleOCR
is not included. Use RapidOCR or Apple Vision for an installation without these tools.

Application logs: `~/Library/Logs/USTA/usta.log`.
User settings: `~/Library/Application Support/usta/`.


## Release regression check

```sh
USTA_REQUIRE_MACOS_APP=1 .venv/bin/python -m unittest tests.packaging.test_macos_bundle -v
```

Set `USTA_MACOS_APP` to check another installed or mounted USTA.app. The check
must show `MacOS` as the screen engine and `Apple Vision` in the OCR selector.
The macOS capabilities module is a dynamic import in a namespace-package folder,
so the spec explicitly includes it. Testing the OCR engine directly is insufficient
because the UI list is populated separately by the platform capability resolver.


## Screen capture and repeated permission requests

USTA 0.1.9 captures through ScreenCaptureKit inside the USTA process. It no longer
launches Pillow's external `screencapture` helper for each frame. Screen Recording
authorization is checked before capture; access is requested at most once per
explicit capture attempt. A denial or native capture error stops OCR and delivers
the error to the UI instead of retrying permission requests in the capture loop.
The capture implementation uses the macOS 15.2+ region API; the current DMG still
requires macOS 26+ because of its embedded Python runtime.

Ad-hoc builds have no stable Developer ID signing identity. After replacing such
a build, macOS can require access to be granted again even when an old USTA entry
is enabled. Quit USTA, turn its Screen Recording access off and on for the current
copy in Applications, then reopen it. USTA does not reset or change privacy grants.

### Enabled toggle but capture still denied after an update

An enabled privacy toggle can still reference a previous ad-hoc code hash.
Confirm this in the macOS TCC unified log: `Failed to match existing code
requirement` for `com.sedataym.usta` and `kTCCServiceScreenCapture`, followed by
different old/current `cdhash` values. `codesign --verify` can succeed at the
same time; bundle integrity and the saved privacy requirement are separate checks.

Quit USTA, then use the supported per-app reset (not a reset of every application's
permissions):

```sh
tccutil reset ScreenCapture com.sedataym.usta
open /Applications/USTA.app
```

Press Start and grant screen recording access again to the installed copy. Use
Quit & Reopen if macOS requests it. The user must grant access; neither the app
nor the build script should edit TCC databases or programmatically grant access.

For subsequent releases, use a stable Apple Development/Developer ID signing
identity. Ad-hoc builds use code-hash requirements and should not be described
as retaining permissions across updates. Test grants by launching the installed
bundle with Launch Services; direct execution from a terminal can test the
terminal's responsibility chain instead of the GUI application's own permission.
