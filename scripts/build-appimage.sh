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

should_bundle_library() {
  local library_path="$1"
  local library_name
  library_name="$(basename "${library_path}")"

  [[ "${library_path}" = /* && -f "${library_path}" ]] || return 1

  case "${library_name}" in
    ld-linux*.so*|ld-musl*.so*|libanl.so*|libBrokenLocale.so*|libc.so*|libdl.so*|libm.so*|libmvec.so*|libnsl.so*|libnss_*.so*|libpthread.so*|libresolv.so*|librt.so*|libthread_db.so*|libutil.so*)
      return 1
      ;;
    libGL.so*|libEGL.so*|libGLX.so*|libOpenGL.so*|libdrm.so*|libgbm.so*|libwayland-*.so*|libX11.so*|libX11-xcb.so*|libxcb*.so*|libxkbcommon*.so*|libfontconfig.so*|libfreetype.so*|libdbus-1.so*|libgdk*.so*|libgtk*.so*)
      return 1
      ;;
  esac

  return 0
}

copy_shared_library_with_links() {
  local source_path="$1"
  local dest_dir="$2"

  [[ -n "${source_path}" && -e "${source_path}" ]] || return 1
  mkdir -p "${dest_dir}"

  local real_source
  real_source="$(readlink -f "${source_path}")"
  cp -a "${real_source}" "${dest_dir}/"

  local source_name real_name
  source_name="$(basename "${source_path}")"
  real_name="$(basename "${real_source}")"
  if [[ "${source_name}" != "${real_name}" && ! -e "${dest_dir}/${source_name}" ]]; then
    ln -s "${real_name}" "${dest_dir}/${source_name}"
  fi
}

bundle_native_dependencies() {
  local scan_root="$1"
  local dest_dir="$2"
  local pass=1

  command -v ldd >/dev/null 2>&1 || return 0

  while (( pass <= 6 )); do
    local copied=0
    local -a scan_files=()
    while IFS= read -r -d '' file_path; do
      scan_files+=("${file_path}")
    done < <(find "${scan_root}" "${dest_dir}" -type f \( -perm -0100 -o -name '*.so' -o -name '*.so.*' \) -print0 2>/dev/null)

    local file_path dependency_path
    for file_path in "${scan_files[@]}"; do
      while IFS= read -r dependency_path; do
        should_bundle_library "${dependency_path}" || continue
        if [[ ! -e "${dest_dir}/$(basename "${dependency_path}")" ]]; then
          echo "Bundling native dependency $(basename "${dependency_path}") from ${dependency_path}"
          copy_shared_library_with_links "${dependency_path}" "${dest_dir}"
          copied=1
        fi
      done < <(ldd "${file_path}" 2>/dev/null | awk '/=>[[:space:]]*\// { print $3 } /^[[:space:]]*\// { print $1 }' | awk 'NF && !seen[$0]++')
    done

    (( copied == 1 )) || break
    (( pass++ ))
  done
}

copy_python_library_candidate() {
  local source_path="$1"
  local dest_dir="$2"

  [[ -n "${source_path}" && -e "${source_path}" ]] || return 1
  mkdir -p "${dest_dir}"

  local current="${source_path}"
  while [[ -L "${current}" ]]; do
    cp -a "${current}" "${dest_dir}/"
    local link_target
    link_target="$(readlink "${current}")"
    if [[ "${link_target}" = /* ]]; then
      current="${link_target}"
    else
      current="$(dirname "${current}")/${link_target}"
    fi
  done

  cp -a "${current}" "${dest_dir}/"
}

find_python_library() {
  local python_exe="$1"
  local libdir="$2"
  local ldlibrary="$3"
  local instsoname="$4"

  if command -v ldd >/dev/null 2>&1; then
    ldd "${python_exe}" 2>/dev/null | awk '/libpython[0-9.]*.*\.so/ { for (i = 1; i <= NF; i++) if ($i ~ /^\//) { print $i; exit } }'
  fi

  for candidate in \
    "${libdir}/${ldlibrary}" \
    "${libdir}/${instsoname}" \
    "$(dirname "${python_exe}")/../lib/${ldlibrary}" \
    "$(dirname "${python_exe}")/../lib/${instsoname}"; do
    [[ -n "${candidate}" && -f "${candidate}" && "$(basename "${candidate}")" == libpython*.so* ]] && printf '%s\n' "${candidate}"
  done
}

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
  "${APPDIR}/usr/lib" \
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

PYTHON_METADATA="$(${PYTHON_BIN} - <<'PY'
import os
import sys
import sysconfig

version = f"{sys.version_info.major}.{sys.version_info.minor}"
dynload = os.path.join(sysconfig.get_path("stdlib") or "", "lib-dynload")
paths = {
    "version": version,
    "executable": os.path.realpath(sys.executable),
    "prefix": sys.prefix,
    "base_prefix": sys.base_prefix,
    "stdlib": sysconfig.get_path("stdlib") or "",
    "platstdlib": sysconfig.get_path("platstdlib") or "",
    "dynload": dynload if os.path.isdir(dynload) else "",
    "libdir": sysconfig.get_config_var("LIBDIR") or "",
    "ldlibrary": sysconfig.get_config_var("LDLIBRARY") or "",
    "instsoname": sysconfig.get_config_var("INSTSONAME") or "",
}
for key, value in paths.items():
    print(f"{key}={value}")
PY
)"

PYTHON_VERSION="$(printf '%s\n' "${PYTHON_METADATA}" | awk -F= '$1 == "version" { print $2; exit }')"
PYTHON_STDLIB="$(printf '%s\n' "${PYTHON_METADATA}" | awk -F= '$1 == "stdlib" { print substr($0, index($0, "=") + 1); exit }')"
PYTHON_PLATSTDLIB="$(printf '%s\n' "${PYTHON_METADATA}" | awk -F= '$1 == "platstdlib" { print substr($0, index($0, "=") + 1); exit }')"
PYTHON_DYNLOAD="$(printf '%s\n' "${PYTHON_METADATA}" | awk -F= '$1 == "dynload" { print substr($0, index($0, "=") + 1); exit }')"
PYTHON_LIBDIR="$(printf '%s\n' "${PYTHON_METADATA}" | awk -F= '$1 == "libdir" { print substr($0, index($0, "=") + 1); exit }')"
PYTHON_LDLIBRARY="$(printf '%s\n' "${PYTHON_METADATA}" | awk -F= '$1 == "ldlibrary" { print substr($0, index($0, "=") + 1); exit }')"
PYTHON_INSTSONAME="$(printf '%s\n' "${PYTHON_METADATA}" | awk -F= '$1 == "instsoname" { print substr($0, index($0, "=") + 1); exit }')"
PYTHON_RUNTIME_DIR="${APPDIR}/usr/lib/python${PYTHON_VERSION}"

if [[ -z "${PYTHON_VERSION}" || -z "${PYTHON_STDLIB}" || ! -d "${PYTHON_STDLIB}" ]]; then
  cat >&2 <<EOF
Unable to locate the Python standard library for ${PYTHON_BIN}.

Collected metadata:
${PYTHON_METADATA}

The AppImage build cannot be made independent of the host Python runtime without
bundling the matching standard library.
EOF
  exit 1
fi

echo "Bundling Python ${PYTHON_VERSION} runtime from ${PYTHON_STDLIB} into ${PYTHON_RUNTIME_DIR}"
mkdir -p "${PYTHON_RUNTIME_DIR}"
cp -a "${PYTHON_STDLIB}/." "${PYTHON_RUNTIME_DIR}/"

if [[ -n "${PYTHON_PLATSTDLIB}" && -d "${PYTHON_PLATSTDLIB}" && "$(readlink -f "${PYTHON_PLATSTDLIB}")" != "$(readlink -f "${PYTHON_STDLIB}")" ]]; then
  if [[ -d "${PYTHON_PLATSTDLIB}/lib-dynload" && ! -d "${PYTHON_RUNTIME_DIR}/lib-dynload" ]]; then
    echo "Copying Python platform native modules from ${PYTHON_PLATSTDLIB}/lib-dynload"
    cp -a "${PYTHON_PLATSTDLIB}/lib-dynload" "${PYTHON_RUNTIME_DIR}/lib-dynload"
  else
    echo "Skipping Python platform stdlib merge from ${PYTHON_PLATSTDLIB}; wheel packages are installed separately into usr/app/site-packages"
  fi
fi

find "${PYTHON_RUNTIME_DIR}" -type d -name __pycache__ -prune -exec rm -rf {} +

if [[ -z "${PYTHON_DYNLOAD}" || ! -d "${PYTHON_RUNTIME_DIR}/lib-dynload" ]]; then
  cat >&2 <<EOF
Unable to locate Python native extension modules for ${PYTHON_BIN}.

Collected metadata:
${PYTHON_METADATA}

The bundled runtime needs lib-dynload modules for standard-library imports such
as ssl, ctypes, sqlite3, compression modules, and other native Python modules.
EOF
  exit 1
fi

PYTHON_LIB_SOURCE=""
while IFS= read -r candidate; do
  [[ -n "${candidate}" ]] || continue
  if [[ -z "${PYTHON_LIB_SOURCE}" ]]; then
    PYTHON_LIB_SOURCE="${candidate}"
  fi
done < <(find_python_library "${PYTHON_REAL}" "${PYTHON_LIBDIR}" "${PYTHON_LDLIBRARY}" "${PYTHON_INSTSONAME}" | awk 'NF && !seen[$0]++')

if [[ -z "${PYTHON_LIB_SOURCE}" || ! -e "${PYTHON_LIB_SOURCE}" ]]; then
  cat >&2 <<EOF
Unable to locate the shared Python library required by ${PYTHON_REAL}.

Expected a libpython*.so* file from one of these metadata values:
  LIBDIR=${PYTHON_LIBDIR}
  LDLIBRARY=${PYTHON_LDLIBRARY}
  INSTSONAME=${PYTHON_INSTSONAME}

Without bundling libpython, the AppImage may fail on systems that do not have
the same Python runtime installed, such as a Python 3.12 system running a
Python ${PYTHON_VERSION}-built AppImage.
EOF
  exit 1
fi

echo "Bundling Python shared library from ${PYTHON_LIB_SOURCE}"
copy_python_library_candidate "${PYTHON_LIB_SOURCE}" "${APPDIR}/usr/lib"

PYTHON_LIB_BASENAME="$(basename "$(readlink -f "${PYTHON_LIB_SOURCE}")")"
for expected_name in "${PYTHON_LDLIBRARY}" "${PYTHON_INSTSONAME}"; do
  if [[ -n "${expected_name}" && ! -e "${APPDIR}/usr/lib/${expected_name}" ]]; then
    ln -s "${PYTHON_LIB_BASENAME}" "${APPDIR}/usr/lib/${expected_name}"
  fi
done

echo "Bundling native dependencies required by Python runtime and wheel extensions"
bundle_native_dependencies "${APPDIR}/usr" "${APPDIR}/usr/lib"
if compgen -G "${APPDIR}/usr/lib/libbz2.so*" >/dev/null; then
  :
elif compgen -G "/usr/lib/libbz2.so*" >/dev/null; then
  copy_shared_library_with_links "$(compgen -G "/usr/lib/libbz2.so*" | sort -V | tail -n 1)" "${APPDIR}/usr/lib"
elif compgen -G "/usr/lib64/libbz2.so*" >/dev/null; then
  copy_shared_library_with_links "$(compgen -G "/usr/lib64/libbz2.so*" | sort -V | tail -n 1)" "${APPDIR}/usr/lib"
fi

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

echo "Validating bundled Python runtime"
APPDIR="${APPDIR}" \
LD_LIBRARY_PATH="${APPDIR}/usr/lib:${APPDIR}/usr/lib64:${LD_LIBRARY_PATH:-}" \
PYTHONHOME="${APPDIR}/usr" \
PYTHONPATH="${APPDIR}/usr/app:${APPDIR}/usr/app/site-packages" \
PYTHONNOUSERSITE=1 \
"${APPDIR}/usr/bin/python3" - <<'PY'
import ctypes
import encodings
import importlib
import ssl
import sys

importlib.import_module("src.main")
print(f"Bundled Python runtime OK: {sys.version.split()[0]}")
PY

if command -v ldd >/dev/null 2>&1; then
  if LD_LIBRARY_PATH="${APPDIR}/usr/lib:${APPDIR}/usr/lib64:${LD_LIBRARY_PATH:-}" ldd "${APPDIR}/usr/bin/python3" 2>/dev/null | grep -E 'libpython[0-9.]*.*\.so' | grep -vq "${APPDIR}/usr/lib"; then
    cat >&2 <<EOF
Bundled Python validation failed: usr/bin/python3 does not resolve libpython
from ${APPDIR}/usr/lib.
EOF
    LD_LIBRARY_PATH="${APPDIR}/usr/lib:${APPDIR}/usr/lib64:${LD_LIBRARY_PATH:-}" ldd "${APPDIR}/usr/bin/python3" >&2 || true
    exit 1
  fi
fi

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
Python executable, libpython, standard library, native Python extension modules, and Python
wheel dependencies are bundled in the AppImage.
See docs/appimage.md for details.
EOF
