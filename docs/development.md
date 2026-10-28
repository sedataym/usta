# Development

Use the setup and checks in [CONTRIBUTING](../CONTRIBUTING.md). Python 3.10 is the declared language/API floor, correcting the former inaccurate 3.8 claim. The local cleanup is verified on Python 3.14; other interpreter/native dependency combinations need their own install evidence. ML wheels may have narrower platform/interpreter availability.

Runtime dependencies are declared in `pyproject.toml`; `requirements.txt` delegates to the same source. The `dev` extra contains checks/build tooling, and `paddle` contains the opt-in Paddle dependencies. Version metadata comes from `usta._version` without importing the GUI.

Use `python -m build` to produce wheel and sdist. After a build run `python -m unittest tests.packaging.test_artifacts -v` to inspect all resource bytes in both artifacts. Packaging validation must also install a wheel into a fresh environment and import from outside the repository.

The AppImage script installs the same project metadata once and starts `python -m usta`. Desktop services, native OCR executables and host GStreamer remain system dependencies. See [AppImage](appimage.md).

Ruff checks imports, unused values and syntax/style correctness; its formatter provides one consistent layout. Mypy currently checks settings/results/storage boundaries; expand coverage as native SDK annotations become practical. Avoid broad suppressions for the entire codebase.
