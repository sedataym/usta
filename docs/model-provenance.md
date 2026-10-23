# OCR model provenance

The ONNX files under `src/usta/resources/ocr_models/rapidocr` were already present in this repository before the cleanup. They were moved without changing their bytes. Filenames identify PP-OCR language/model variants, but this checkout does not include per-file download URLs, licenses, or original checksums.

Exact upstream provenance and redistribution terms are **not yet verified**. Do not infer a model license from USTA's MIT source license. Before publishing redistributed artifacts, maintainers should record each original model URL/revision, its license/notice requirements and SHA-256. Wheel/sdist tests preserve the repository's current bytes; they do not establish licensing provenance.
