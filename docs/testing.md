# Testing

Run portable tests with `QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v`. Native tests are opt-in: in a real macOS desktop session use `USTA_NATIVE_TESTS=1 python -m unittest discover -s tests/native -v` and the native Vision/keyboard classes under tests/unit. Do not set offscreen for native tests. Skips do not prove platform compatibility. Unit tests must not call live translation APIs or download OCR models.

The sandbox used by desktop automation may deny Unix socket bind and native Cocoa/Vision services. Run the suite outside that sandbox when this occurs; do not skip a failed IPC test as if it passed. The 23 October 2026 local native run passed all 59 tests before final acceptance regressions were added. CI uses offscreen Qt and leaves actual fullscreen/permission interactions to opt-in native acceptance.

After building, `USTA_REQUIRE_ARTIFACTS=1 python -m unittest tests.packaging.test_artifacts -v` checks resource hashes in the wheel/sdist. The package workflow installs a wheel in a fresh environment outside the repository.
