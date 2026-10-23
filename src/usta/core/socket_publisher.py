import logging
import os
import json
import socket
import threading
import time
from usta.config import SOCKET_PATH

logger = logging.getLogger(__name__)


class TranslationPublisher:
    """Unix domain socket server that broadcasts translation results to all connected clients.

    Sends JSON messages (one per line) for each translation.
    """

    def __init__(self):
        self._server_socket: socket.socket | None = None
        self._clients: list[socket.socket] = []
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the Unix socket server in a background thread."""
        if self._running:
            return

        # Clean up stale socket file
        if os.path.exists(SOCKET_PATH):
            try:
                os.unlink(SOCKET_PATH)
            except OSError:
                pass

        self._server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server_socket.bind(SOCKET_PATH)
        self._server_socket.listen(5)
        self._server_socket.settimeout(1.0)  # Allows graceful shutdown via _running flag

        self._running = True
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._thread.start()
        logger.info(f"TranslationPublisher: Listening on {SOCKET_PATH}")

    def stop(self) -> None:
        """Stop the server, close all client connections, and clean up the socket file."""
        self._running = False

        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

        with self._lock:
            for client in self._clients:
                try:
                    client.close()
                except OSError:
                    pass
            self._clients.clear()

        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass
            self._server_socket = None

        if os.path.exists(SOCKET_PATH):
            try:
                os.unlink(SOCKET_PATH)
            except OSError:
                pass

        logger.info("TranslationPublisher: Stopped.")

    def broadcast(self, original: str, translated: str,
                  source_lang: str = "en", target_lang: str = "tr",
                  engine: str = "unknown") -> None:
        """Send a translation result to all connected clients as a JSON line.

        Args:
            original: The original (source) text.
            translated: The translated text.
            source_lang: Source language code.
            target_lang: Target language code.
            engine: Name of the translation engine used.
        """
        message = json.dumps({
            "original": original,
            "translated": translated,
            "source": source_lang,
            "target": target_lang,
            "engine": engine,
            "timestamp": time.time(),
        }) + "\n"

        data = message.encode("utf-8")

        with self._lock:
            disconnected = []
            for client in self._clients:
                try:
                    client.sendall(data)
                except (BrokenPipeError, OSError):
                    disconnected.append(client)

            for client in disconnected:
                self._clients.remove(client)
                try:
                    client.close()
                except OSError:
                    pass

    def _accept_loop(self) -> None:
        """Main loop that accepts incoming client connections."""
        while self._running:
            try:
                conn, _ = self._server_socket.accept()
                with self._lock:
                    self._clients.append(conn)
                logger.info(f"TranslationPublisher: Client connected ({len(self._clients)} total)")
            except socket.timeout:
                continue
            except OSError:
                if self._running:
                    logger.error("TranslationPublisher: Accept error, retrying…")
                break