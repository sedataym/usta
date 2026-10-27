"""RapidOCR 1.2 loads its detector/recognizer by bare names from its package path."""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = collect_submodules("rapidocr_onnxruntime")
datas = collect_data_files("rapidocr_onnxruntime")
# RapidOCR appends its package directory to sys.path and imports names from YAML.
# Keep real package __init__.py files so these imports do not become empty namespaces.
module_collection_mode = "pyz+py"
