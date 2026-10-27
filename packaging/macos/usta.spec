# -*- mode: python ; coding: utf-8 -*-
import os
import runpy
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

root = Path(SPECPATH).resolve().parents[1]
version = runpy.run_path(str(root / "src/usta/_version.py"))["__version__"]
icon = root / "build/macos/USTA.icns"
datas = collect_data_files("usta")
datas += collect_data_files("easyocr")
hidden = collect_submodules("usta") + [
    "check_bundle",
    # Loaded by name; pkgutil collection skips this namespace-package directory.
    "usta.core.platform.macos.capabilities",
    "pynput.keyboard._darwin",
    "pynput.mouse._darwin",
    "AppKit", "Foundation", "Quartz", "Vision", "CoreML", "ApplicationServices", "CoreText",
    "ScreenCaptureKit",
]
analysis = Analysis(
    [str(root / "packaging/macos/launcher.py")],
    pathex=[str(root / "src"), str(root / "packaging/macos")],
    # torchvision 0.29+ loads _C_stable.so via torch.ops rather than a Python import.
    binaries=collect_dynamic_libs("torchvision", search_patterns=["*.so", "*.dylib"]),
    datas=datas,
    hiddenimports=hidden,
    hookspath=[str(root / "packaging/macos/hooks")],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "IPython", "notebook", "tkinter", "matplotlib", "paddle", "paddleocr"],
    noarchive=False,
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz, analysis.scripts, [],
    exclude_binaries=True,
    name="USTA",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    argv_emulation=False,
    target_arch="arm64",
    codesign_identity=os.environ.get("USTA_CODESIGN_IDENTITY") or None,
    entitlements_file=None,
)
collection = COLLECT(exe, analysis.binaries, analysis.datas, strip=False, upx=False, name="USTA")
app = BUNDLE(
    collection,
    name="USTA.app",
    icon=str(icon),
    bundle_identifier="com.sedataym.usta",
    version=version,
    info_plist={
        "CFBundleDisplayName": "USTA",
        "CFBundleShortVersionString": version,
        "CFBundleVersion": version,
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "26.0",
        "NSPrincipalClass": "NSApplication",
        "LSApplicationCategoryType": "public.app-category.utilities",
    },
)
