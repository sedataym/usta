"""Bounded, non-blocking Unix socket translation broadcast."""

import errno
import json
import logging
import queue
import select
import socket
import stat
import threading
import time
from pathlib import Path

from usta.config import SOCKET_PATH

logger = logging.getLogger(__name__)


class TranslationPublisher:
    MAX_PENDING_BYTES = 1024 * 1024

    def __init__(self, path=None):
        self.path = Path(path or SOCKET_PATH)
        self._messages = queue.Queue(maxsize=256)
        self._stopped = threading.Event()
        self._stopped.set()
        self._thread = None
        self._server = None
        self._identity = None

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        if self.path.exists():
            identity = self.path.lstat()
            if not stat.S_ISSOCK(identity.st_mode):
                raise OSError(errno.EADDRINUSE, "IPC path is not a socket")
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as probe:
                probe.settimeout(0.2)
                try:
                    probe.connect(str(self.path))
                except OSError as exc:
                    if exc.errno != errno.ECONNREFUSED:
                        raise
                else:
                    raise OSError(errno.EADDRINUSE, "USTA IPC socket is already in use")
            if self.path.lstat().st_ino != identity.st_ino:
                raise OSError(errno.EADDRINUSE, "IPC path changed during startup")
            self.path.unlink()
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            server.bind(str(self.path))
            server.listen(5)
            server.setblocking(False)
        except OSError:
            server.close()
            raise
        self._server = server
        self._identity = self.path.stat().st_ino
        self._messages = queue.Queue(maxsize=256)
        self._stopped.clear()
        self._thread = threading.Thread(target=self._run, name="usta-ipc", daemon=True)
        self._thread.start()

    def stop(self):
        self._stopped.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            if self._thread.is_alive():
                logger.error("IPC thread did not stop within deadline")
                return
            self._thread = None
        if self._server is not None:
            self._server.close()
            self._server = None
        if self._identity is not None:
            try:
                if self.path.lstat().st_ino == self._identity:
                    self.path.unlink()
            except FileNotFoundError:
                pass
            self._identity = None

    def broadcast(self, original, translated, source_lang="en", target_lang="tr", engine="unknown"):
        if self._stopped.is_set():
            return
        data = (
            json.dumps(
                {
                    "original": original,
                    "translated": translated,
                    "source": source_lang,
                    "target": target_lang,
                    "engine": engine,
                    "timestamp": time.time(),
                }
            )
            + "\n"
        ).encode("utf-8")
        try:
            self._messages.put_nowait(data)
        except queue.Full:
            logger.warning("IPC queue full; dropping broadcast")

    def _run(self):
        clients = {}
        try:
            while not self._stopped.is_set():
                readable, writable, _ = select.select(
                    [self._server], [c for c, pending in clients.items() if pending], [], 0.05
                )
                if readable:
                    while True:
                        try:
                            client, _ = self._server.accept()
                            client.setblocking(False)
                            clients[client] = bytearray()
                        except BlockingIOError:
                            break
                while True:
                    try:
                        data = self._messages.get_nowait()
                    except queue.Empty:
                        break
                    for client in list(clients):
                        pending = clients[client]
                        if len(pending) + len(data) > self.MAX_PENDING_BYTES:
                            client.close()
                            del clients[client]
                        else:
                            pending.extend(data)
                for client in writable:
                    if client not in clients:
                        continue
                    try:
                        sent = client.send(clients[client])
                        if sent == 0:
                            raise ConnectionError("IPC peer closed")
                        del clients[client][:sent]
                    except BlockingIOError:
                        pass
                    except OSError:
                        client.close()
                        del clients[client]
        except OSError:
            if not self._stopped.is_set():
                logger.exception("IPC loop failed")
        finally:
            for client in clients:
                client.close()
