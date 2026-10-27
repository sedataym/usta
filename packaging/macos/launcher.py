"""Finder entry point and offline diagnostics for the macOS application bundle."""

import logging
import multiprocessing
import sys
from pathlib import Path


def main():
    multiprocessing.freeze_support()
    if len(sys.argv) == 3 and sys.argv[1] == "--check-bundle":
        from check_bundle import check_bundle

        return check_bundle(Path(sys.argv[2]))

    log_dir = Path.home() / "Library" / "Logs" / "USTA"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_dir / "usta.log", encoding="utf-8")],
    )
    from usta.main import main as run

    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
