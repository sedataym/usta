# Architecture

The installed package is `usta`, in `src/usta`. `usta`, `python -m usta` and the repository's `run.py` enter `usta.main.main`. Main configures logging and runtime directories before creating Qt widgets.

- `application` contains persistent value models, typed translation jobs/results, controllers, the capture pipeline and its Qt thread adapter.
- `core/ocr` and `core/translation` implement existing providers. The lazy registry gives capability lists and manager factories one naming source. Backend `read_text` remains a string boundary; pipeline input uses `OCRResult` and translation requests/results carry immutable session metadata.
- `core/screenshot` owns native capture, including Portal/PipeWire/GStreamer state. Native implementations load only when selected. `core/platform` resolves OS/desktop-specific overrides.
- `infrastructure` owns atomic storage, primitive-only legacy migration, runtime paths, logging and Unix socket broadcasting.
- `ui` owns widgets, settings presentation, region selector windows and Cocoa window helpers. Tabs own their widgets and emit actions; they do not access worker internals. Core engines must not import UI.
- `resources` contains unchanged ONNX models and gettext catalogs. `resource_paths` retains extracted installed resources for the application lifetime.

## Thread ownership

The GUI submits immutable settings to the worker. Its capture loop owns screenshot and OCR instances. One translation executor creates a separate translator for each immutable job. Session identifiers invalidate results after stop or configuration change. GUI stop requests do not wait on the network; closing the window waits asynchronously for capture cleanup. Socket I/O runs on its own thread with bounded queues and per-client pending bytes.

## Persistence

Settings/presets use schema-versioned JSON under the existing platform config directory. Writes use a private temporary file and atomic replacement. Legacy local pickle files are read using a globals-rejecting unpickler and remain untouched after migration. Unsupported/corrupt JSON is preserved rather than silently overwritten. Downgrading does not backport later JSON edits to the old pickle files.
