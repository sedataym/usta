#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_NAME="usta"
VENV_DIR="${VENV_DIR:-${ROOT_DIR}/.venv}"
PYTHON_BIN="${PYTHON_BIN:-${VENV_DIR}/bin/python}"
ARCH="${ARCH:-$(uname -m)}"
BUILD_DIR="${BUILD_DIR:-${ROOT_DIR}/build/appimage}"
APPDIR="${APPDIR:-${BUILD_DIR}/${APP_NAME}.AppDir}"
DIST_DIR="${DIST_DIR:-${ROOT_DIR}/dist}"
APPIMAGETOOL="${APPIMAGETOOL:-appimagetool}"
DOWNLOAD_APPIMAGETOOL="${DOWNLOAD_APPIMAGETOOL:-1}"

case "${ARCH}" in
  x86_64|amd64) APPIMAGE_ARCH="x86_64" ;;
  aarch64|arm64) APPIMAGE_ARCH="aarch64" ;;
  *) APPIMAGE_ARCH="${ARCH}" ;;
esac

cd "${ROOT_DIR}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  cat >&2 <<EOF
Missing project virtualenv Python: ${PYTHON_BIN}

Create or refresh the project virtualenv before building:
  python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip setuptools wheel
  .venv/bin/python -m pip install -r requirements.txt

Or pass an explicit virtualenv Python:
  PYTHON_BIN=/path/to/venv/bin/python ./scripts/build-appimage.sh
EOF
  exit 1
fi

APP_VERSION="${APP_VERSION:-$(${PYTHON_BIN} - <<'PY'
import re
from pathlib import Path

config = Path("src/config.py").read_text(encoding="utf-8")
match = re.search(r'^APP_VERSION\s*=\s*["\']([^"\']+)["\']', config, re.M)
print(match.group(1) if match else "0.0.0")
PY
)}"

if ! command -v "${APPIMAGETOOL}" >/dev/null 2>&1; then
  LOCAL_APPIMAGETOOL="${BUILD_DIR}/appimagetool-${APPIMAGE_ARCH}.AppImage"
  if [[ "${DOWNLOAD_APPIMAGETOOL}" != "1" ]]; then
    cat >&2 <<EOF
Missing appimagetool.

Install it from your distribution or download the AppImage release, then run for example:
  APPIMAGETOOL=/path/to/appimagetool-${APPIMAGE_ARCH}.AppImage ./scripts/build-appimage.sh

Or allow this script to download it automatically:
  DOWNLOAD_APPIMAGETOOL=1 ./scripts/build-appimage.sh
EOF
    exit 1
  fi

  mkdir -p "${BUILD_DIR}"
  if [[ ! -x "${LOCAL_APPIMAGETOOL}" ]]; then
    command -v curl >/dev/null 2>&1 || {
      echo "Missing appimagetool and curl is not available to download it automatically." >&2
      exit 1
    }
    echo "Downloading appimagetool to ${LOCAL_APPIMAGETOOL}"
    curl -L --fail \
      "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${APPIMAGE_ARCH}.AppImage" \
      -o "${LOCAL_APPIMAGETOOL}"
    chmod +x "${LOCAL_APPIMAGETOOL}"
  fi
  APPIMAGETOOL="${LOCAL_APPIMAGETOOL}"
fi

rm -rf "${APPDIR}"
mkdir -p \
  "${APPDIR}/usr/bin" \
  "${APPDIR}/usr/app" \
  "${APPDIR}/usr/app/site-packages" \
  "${APPDIR}/usr/share/applications" \
  "${APPDIR}/usr/share/icons/hicolor/256x256/apps" \
  "${DIST_DIR}"

echo "Installing Python package payload from ${PYTHON_BIN} into ${APPDIR}/usr/app/site-packages"
"${PYTHON_BIN}" -m pip install --upgrade pip setuptools wheel
"${PYTHON_BIN}" -m pip install --upgrade --target "${APPDIR}/usr/app/site-packages" -r requirements.txt
"${PYTHON_BIN}" -m pip install --upgrade --target "${APPDIR}/usr/app/site-packages" .

PYTHON_REAL="$(${PYTHON_BIN} -c 'import sys; print(sys.executable)')"
cp "${PYTHON_REAL}" "${APPDIR}/usr/bin/python3"

cat > "${APPDIR}/usr/bin/usta" <<'EOF'
#!/usr/bin/env bash
APPDIR="$(dirname "$(dirname "$(readlink -f "${0}")")")/.."
exec "${APPDIR}/AppRun" "$@"
EOF
chmod +x "${APPDIR}/usr/bin/usta"

cp "${ROOT_DIR}/packaging/appimage/AppRun" "${APPDIR}/AppRun"
chmod +x "${APPDIR}/AppRun" "${APPDIR}/usr/bin/python3"

cp "${ROOT_DIR}/packaging/appimage/usta.desktop" "${APPDIR}/usta.desktop"
cp "${ROOT_DIR}/packaging/appimage/usta.desktop" "${APPDIR}/usr/share/applications/usta.desktop"
cp "${ROOT_DIR}/src/ui/assets/usta.png" "${APPDIR}/usta.png"
cp "${ROOT_DIR}/src/ui/assets/usta.png" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/usta.png"

OUTPUT="${DIST_DIR}/USTA-${APP_VERSION}-${APPIMAGE_ARCH}.AppImage"
rm -f "${OUTPUT}"

echo "Building ${OUTPUT}"
ARCH="${APPIMAGE_ARCH}" "${APPIMAGETOOL}" "${APPDIR}" "${OUTPUT}"
chmod +x "${OUTPUT}"

cat <<EOF
Built: ${OUTPUT}

Runtime system dependencies are still required for desktop integration and OCR backends:
  xdg-desktop-portal, an xdg-desktop-portal backend, PipeWire, GStreamer PipeWire plugins,
  tesseract plus language packs, and optionally spectacle/slurp depending on selected engines.
See docs/appimage.md for details.
EOF
