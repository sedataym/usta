#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-${ROOT_DIR}/.venv/bin/python}"
BUILD_DIR="${ROOT_DIR}/build/macos"
DIST_DIR="${ROOT_DIR}/dist/macos"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "This build configuration requires an Apple Silicon Mac." >&2
  exit 1
fi
"${PYTHON_BIN}" -c 'import PyInstaller' || {
  echo "Install the build tool: ${PYTHON_BIN} -m pip install 'pyinstaller>=6.16,<7'" >&2
  exit 1
}
SIGNING_MODE="${USTA_SIGNING_MODE:-developer-id}"
RESOLVED_IDENTITY="$("${PYTHON_BIN}" "${ROOT_DIR}/packaging/macos/signing_policy.py")"
export USTA_CODESIGN_IDENTITY="${RESOLVED_IDENTITY}"
if [[ "${RESOLVED_IDENTITY}" != "-" && "${SIGNING_MODE}" != "self-signed" ]]; then
  : "${USTA_NOTARY_PROFILE:?Set USTA_NOTARY_PROFILE to a notarytool Keychain profile for distribution.}"
  xcrun --find notarytool >/dev/null
  xcrun --find stapler >/dev/null
  # Validate credentials before the expensive build; credentials remain in Keychain.
  xcrun notarytool history --keychain-profile "${USTA_NOTARY_PROFILE}" --output-format json >/dev/null
fi
mkdir -p "${BUILD_DIR}" "${DIST_DIR}"
cd "${ROOT_DIR}"
APP_VERSION="$(${PYTHON_BIN} -c 'from usta._version import __version__; print(__version__)')"

"${PYTHON_BIN}" - "${ROOT_DIR}/src/usta/ui/assets/usta.png" "${BUILD_DIR}/USTA.icns" <<'PY'
import sys
from PIL import Image
Image.open(sys.argv[1]).resize((1024, 1024)).save(sys.argv[2], format="ICNS")
PY
export PYINSTALLER_CONFIG_DIR="${BUILD_DIR}/pyinstaller-cache"
"${PYTHON_BIN}" -m PyInstaller --noconfirm \
  --workpath "${BUILD_DIR}/pyinstaller" --distpath "${DIST_DIR}" \
  "${ROOT_DIR}/packaging/macos/usta.spec"

if [[ "${SIGNING_MODE}" == "self-signed" ]]; then
  "${PYTHON_BIN}" "${ROOT_DIR}/packaging/macos/signing_policy.py" --sign-app "${DIST_DIR}/USTA.app"
fi
codesign --verify --deep --strict "${DIST_DIR}/USTA.app"
if [[ "${RESOLVED_IDENTITY}" != "-" ]]; then
  "${PYTHON_BIN}" "${ROOT_DIR}/packaging/macos/signing_policy.py" --verify-app "${DIST_DIR}/USTA.app"
fi
if ! "${DIST_DIR}/USTA.app/Contents/MacOS/USTA" --check-bundle "${BUILD_DIR}/bundle-check.json"; then
  cat "${BUILD_DIR}/bundle-check.json" >&2
  exit 1
fi
cat "${BUILD_DIR}/bundle-check.json"
STAGING_DIR="$(mktemp -d "${BUILD_DIR}/dmg-stage.XXXXXX")"
trap 'rm -rf "${STAGING_DIR}"' EXIT
ditto "${DIST_DIR}/USTA.app" "${STAGING_DIR}/USTA.app"
ln -s /Applications "${STAGING_DIR}/Applications"
cp "${ROOT_DIR}/packaging/macos/INSTALL.txt" "${STAGING_DIR}/INSTALL.txt"
if [[ "${SIGNING_MODE}" == "self-signed" ]]; then
  FINAL_DMG_PATH="${DIST_DIR}/USTA-${APP_VERSION}-macOS-arm64-selfsigned.dmg"
  cp "${ROOT_DIR}/packaging/macos/certs/usta-self-signed.cer" "${STAGING_DIR}/USTA-Code-Signing.cer"
  cat > "${STAGING_DIR}/SIGNING.txt" <<'SIGNING'
Signed with the persistent USTA Local Code Signing certificate; not Apple-notarized.
This is a self-signed test build. Apple does not vouch for the publisher.
All updates must use the SAME certificate and private key; public certificate included.
The private key is never distributed. First-install Gatekeeper/permission approval is required.
SIGNING
elif [[ "${RESOLVED_IDENTITY}" == "-" ]]; then
  FINAL_DMG_PATH="${DIST_DIR}/USTA-${APP_VERSION}-macOS-arm64-dev.dmg"
  cat > "${STAGING_DIR}/SIGNING.txt" <<'SIGNING'
Local development build: ad-hoc signed, not Apple-notarized.
Updates can invalidate Screen Recording and Input Monitoring grants.
Use the Developer ID release workflow for distribution to other Macs.
SIGNING
else
  FINAL_DMG_PATH="${DIST_DIR}/USTA-${APP_VERSION}-macOS-arm64.dmg"
  cat > "${STAGING_DIR}/SIGNING.txt" <<'SIGNING'
Distribution build: signed with Developer ID Application and notarized by Apple.
The publisher Team ID and com.sedataym.usta identifier are preserved across releases.
The first transition from an ad-hoc build can require permission to be granted again.
SIGNING
fi
# A rejected/incomplete notarization must never appear under the release filename.
DMG_PATH="${DIST_DIR}/.USTA-${APP_VERSION}-pending.dmg"
hdiutil create -ov -volname "USTA ${APP_VERSION}" -srcfolder "${STAGING_DIR}" \
  -format UDZO -imagekey zlib-level=9 "${DMG_PATH}"
if [[ "${SIGNING_MODE}" == "self-signed" ]]; then
  codesign --force --timestamp=none --sign "${RESOLVED_IDENTITY}" "${DMG_PATH}"
fi
if [[ "${RESOLVED_IDENTITY}" != "-" && "${SIGNING_MODE}" != "self-signed" ]]; then
  codesign --force --timestamp --sign "${RESOLVED_IDENTITY}" "${DMG_PATH}"
  xcrun notarytool submit "${DMG_PATH}" --keychain-profile "${USTA_NOTARY_PROFILE}" \
    --wait --output-format json > "${BUILD_DIR}/notarization.json"
  "${PYTHON_BIN}" - "${BUILD_DIR}/notarization.json" <<'PY_NOTARY'
import json
import sys
with open(sys.argv[1]) as report:
    result = json.load(report)
if result.get("status") != "Accepted":
    raise SystemExit(f"Notarization was not accepted: {result.get('status')}; see {sys.argv[1]}")
PY_NOTARY
  # Apple creates tickets for the DMG and its nested application in one submission.
  xcrun stapler staple "${DIST_DIR}/USTA.app"
  xcrun stapler validate "${DIST_DIR}/USTA.app"
  xcrun stapler staple "${DMG_PATH}"
  xcrun stapler validate "${DMG_PATH}"
  spctl --assess --type open --context context:primary-signature --verbose=2 "${DMG_PATH}"
fi
hdiutil verify "${DMG_PATH}"
mv -f "${DMG_PATH}" "${FINAL_DMG_PATH}"
shasum -a 256 "${FINAL_DMG_PATH}" > "${FINAL_DMG_PATH}.sha256"
echo "Built: ${FINAL_DMG_PATH}"
