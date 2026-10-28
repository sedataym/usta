# Contributing to USTA

USTA uses Python and PySide6. Keep user-visible behavior and Linux/macOS native window rules stable when refactoring.

## Development setup

Create a virtual environment (Linux Portal users need system PyGObject/GStreamer packages and `--system-site-packages`), then run:

```sh
python -m pip install -e '.[dev]'
python run.py
```

Paddle is opt-in: `python -m pip install -e '.[paddle]'`. Its native runtime must be available for your interpreter/architecture. Existing default OCR engines remain installed by the standard setup.

## Before opening a pull request

```sh
ruff check .
ruff format --check .
mypy
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
python -m build
python -m pip check
```

Do not use real translation APIs, private screenshots, or automatic model downloads in unit tests. Regression tests should reproduce a specific user-visible failure. Native desktop tests are opt-in; see [testing](docs/testing.md). Report skipped or unavailable platform checks honestly.

Keep each change focused. Separate mechanical formatting/moves from behavior fixes. Update documentation and translations when changing user-facing text. Never commit API keys, local settings, or screen content.

See [architecture](docs/architecture.md), [development](docs/development.md), and [compatibility](docs/compatibility.md) for module boundaries and release checks.
