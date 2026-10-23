# Testing

Run portable tests with `QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v`. Native tests are opt-in: in a real macOS desktop session use `USTA_NATIVE_TESTS=1 python -m unittest discover -s tests/native -v` and the native Vision/keyboard classes under tests/unit. Do not set offscreen for native tests. Skips do not prove platform compatibility. Unit tests must not call live translation APIs or download OCR models.
