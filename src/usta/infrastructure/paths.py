"""Runtime path policy; resolving paths does not create files."""

import tempfile
from dataclasses import dataclass
from pathlib import Path

from usta.core.platform.capability_resolver import CONFIG_DIR


@dataclass(frozen=True)
class RuntimePaths:
    config_dir: Path
    capture_dir: Path
    socket_path: Path


def resolve_paths() -> RuntimePaths:
    temporary = Path(tempfile.gettempdir())
    return RuntimePaths(
        Path(CONFIG_DIR),
        Path("/dev/shm") if Path("/dev/shm").is_dir() else temporary,
        temporary / "usta.sock",
    )


def prepare_paths(paths: RuntimePaths) -> None:
    paths.config_dir.mkdir(parents=True, exist_ok=True)


class CaptureWorkspace:
    """Only this object's files are removed during cleanup."""

    def __init__(self):
        base = resolve_paths().capture_dir
        self._directory = tempfile.TemporaryDirectory(prefix="usta-", dir=base)
        self.image_path = str(Path(self._directory.name) / "snapshot.jpeg")
        self.fullscreen_path = str(Path(self._directory.name) / "full-screen.jpeg")

    def close(self) -> None:
        self._directory.cleanup()
