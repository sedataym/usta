# macOS DMG

The current recipe builds USTA for **Apple Silicon (arm64), macOS 26 or newer**.
The Python runtime used for this release has a macOS 26 deployment target.
The application includes Python, PySide6, RapidOCR models, Apple Vision bindings,
and the EasyOCR/PyTorch dependencies. No separate Python installation is needed.

## Distribution signing: one-time setup

For distribution to other Macs, enroll in the [Apple Developer Program](https://developer.apple.com/programs/),
then create a [Developer ID Application certificate](https://developer.apple.com/help/account/certificates/create-developer-id-certificates/).
Install the certificate with its matching private key in the build Mac's Keychain.
Use the same Apple Team and `com.sedataym.usta` bundle identifier for subsequent releases.
This is the Apple-trusted distribution path. For the explicitly requested free
self-signed workflow, see below; it is not notarized and has additional first-install steps.

Check the installed identity (the printed SHA-1 fingerprint is public metadata):

```sh
security find-identity -v -p codesigning
```

Store notarization credentials interactively in Keychain; no password goes into the
repository, build script or chat:

```sh
xcrun notarytool store-credentials "usta-notary"
```

Use a current Xcode/Command Line Tools installation containing `notarytool` and
`stapler`. Notarization uses your Apple account; it is separate from user privacy
consent and never grants Screen Recording, Accessibility or Input Monitoring.

## Build a distribution DMG

From an Apple Silicon Mac with the project virtual environment installed:

```sh
.venv/bin/python -m pip install 'pyinstaller>=6.16,<7'
export USTA_CODESIGN_IDENTITY="Developer ID Application: Your Publisher (ABCDE12345)"
export USTA_SIGNING_TEAM_ID="ABCDE12345"
export USTA_NOTARY_PROFILE="usta-notary"
./scripts/build-dmg.sh
```

The script checks that the certificate and private key exist, the certificate is
Developer ID Application, and the configured Team ID matches. It checks notarization
credentials before building. PyInstaller signs the app and embedded libraries with
hardened runtime. The post-build check requires the fixed bundle ID, expected Team
ID and a stable Apple certificate requirement instead of an ad-hoc `cdhash`.

The signed DMG is submitted to Apple. Only an `Accepted` result, successful ticket
stapling/validation and Gatekeeper assessment allow it to be renamed to
`dist/macos/USTA-<version>-macOS-arm64.dmg`. Until then it has a hidden pending filename.
The notarization result is in `build/macos/notarization.json`. The standalone `.app`
and DMG receive their tickets; the DMG's ticket covers the application inside it.
The final SHA-256 checksum is written after stapling.

The disk image contains the application, an Applications shortcut, installation notes
and `SIGNING.txt` describing the build. No separate Python installation is required.
Offline diagnostics verify Qt/SVG resources, translations, dynamic engine imports,
EasyOCR/PyTorch, actual OCR tab engine options and RapidOCR/Apple Vision recognition.
They do not capture the screen, start keyboard listeners or make network calls.
The report is saved to `build/macos/bundle-check.json`.

Set `PYTHON_BIN` to use another compatible project Python environment. The target
remains Apple Silicon/macOS 26+.

## Free persistent self-signed builds

The build Mac has a dedicated `USTA Local Code Signing` identity in its login
Keychain. Its public certificate is `packaging/macos/certs/usta-self-signed.cer`;
`self-signed-identity.json` pins its SHA-1, SHA-256 and bundle identifier. The private
key stays in Keychain and must never be committed or included in a DMG. Back up the
identity, including its private key, securely through Keychain Access before moving
to another build Mac. Restore that identity; do not generate a new certificate for
an update. A lost key means losing continuity with this identity.

```sh
USTA_SIGNING_MODE=self-signed ./scripts/build-dmg.sh
```

This produces `USTA-<version>-macOS-arm64-selfsigned.dmg` and a SHA-256 checksum.
It fails if the pinned certificate/private key is missing or a different identity
is selected. The application and nested code are signed after PyInstaller's initial
ad-hoc assembly. Hardened runtime/library validation is not enabled in this mode:
self-signed certificates have no Apple Team ID. Offline bundle checks still run.

The designated requirement binds `com.sedataym.usta` to the exact pinned certificate,
not a per-build code hash. Updates must preserve this certificate, key, identifier,
and installation path. The DMG includes the **public certificate only** and signing
notes. This is not Apple-trusted or notarized: another Mac can require a Gatekeeper
exception and local certificate trust setup, plus the normal initial privacy grants.
Do not disable Gatekeeper or system protections globally. Certificate trust, when
needed, should be limited to code signing in the user's Keychain, not SSL trust.

Self-signing is intended to stabilize the application identity; permission retention
must be checked on the installed app and may still be affected by macOS policy.
The initial migration from an old ad-hoc app can require granting permissions once
again. Never reset permissions between the two signed versions in an upgrade test.

Read-only privacy diagnostics (no requests, resets or keyboard listener):

```sh
open -n /Applications/USTA.app --args --check-permissions /tmp/usta-permissions.json
```

Wait for the JSON output. It reports the bundle identity, version, executable and
Screen Recording, Accessibility and Input Monitoring preflight results. Launch via
Launch Services as shown; running the executable directly in Terminal can use a
different privacy responsibility chain. Confirm actual capture and shortcuts too.

## Explicit local development build

```sh
USTA_ALLOW_ADHOC=1 ./scripts/build-dmg.sh
```

This opt-in produces `USTA-<version>-macOS-arm64-dev.dmg`, with no notarization.
Ad-hoc code hashes change on rebuild, so privacy permissions may be invalidated.
The regular distribution command refuses to fall back to this mode. Existing
0.1.10 and earlier DMGs remain ad-hoc builds; changing the recipe does not re-sign them.

## Permission continuity

The first transition from an ad-hoc build to the Developer ID build can require a
one-time regrant. Later updates preserve signing identity when the same publisher
Team ID and bundle ID are retained. Apple can still require consent due to system
policy changes, revocation or explicit user resets; signing is not a permission bypass.
Notarization provides Gatekeeper verification, while the stable signing requirement
is what addresses the code-hash mismatch seen in this project.

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

For subsequent releases, use the pinned self-signed identity or a stable
Developer ID signing identity as described above. Ad-hoc builds use code-hash requirements and should not be described
as retaining permissions across updates. Test grants by launching the installed
bundle with Launch Services; direct execution from a terminal can test the
terminal's responsibility chain instead of the GUI application's own permission.
