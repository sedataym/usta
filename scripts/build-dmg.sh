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

codesign --verify --deep --strict "${DIST_DIR}/USTA.app"
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
DMG_PATH="${DIST_DIR}/USTA-${APP_VERSION}-macOS-arm64.dmg"
hdiutil create -ov -volname "USTA ${APP_VERSION}" -srcfolder "${STAGING_DIR}" \
  -format UDZO -imagekey zlib-level=9 "${DMG_PATH}"
hdiutil verify "${DMG_PATH}"
shasum -a 256 "${DMG_PATH}" > "${DMG_PATH}.sha256"
echo "Built: ${DMG_PATH}"
