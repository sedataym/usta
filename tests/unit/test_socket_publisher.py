import json
import socket
import tempfile
import unittest
from pathlib import Path

from usta.infrastructure.socket_publisher import TranslationPublisher


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "usta.sock"
        self.publisher = TranslationPublisher(self.path)
        self.addCleanup(self.publisher.stop)

    def connect(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(str(self.path))
        self.addCleanup(s.close)
        return s

    def test_broadcast_and_restart_preserve_json_contract(self):
        self.publisher.start()
        a = self.connect()
        b = self.connect()
        # Poll via broadcast/read: acceptance is owned by I/O thread.
        self.publisher.broadcast("hello", "merhaba", "en", "tr", "Google")
        for client in (a, b):
            data = json.loads(client.recv(65536).splitlines()[0])
            self.assertEqual(
                set(data), {"original", "translated", "source", "target", "engine", "timestamp"}
            )
            self.assertEqual(data["translated"], "merhaba")
        self.publisher.stop()
        self.assertFalse(self.path.exists())
        self.publisher.start()
        self.assertTrue(self.path.exists())

    def test_second_server_does_not_unlink_active_socket(self):
        self.publisher.start()
        inode = self.path.stat().st_ino
        other = TranslationPublisher(self.path)
        with self.assertRaises(OSError):
            other.start()
        other.stop()
        self.assertEqual(self.path.stat().st_ino, inode)
        self.connect()

    def test_regular_file_is_not_removed(self):
        self.path.write_text("keep")
        with self.assertRaises(OSError):
            self.publisher.start()
        self.publisher.stop()
        self.assertEqual(self.path.read_text(), "keep")

    def test_slow_or_disconnected_reader_cannot_block_broadcast_or_stop(self):
        import time

        self.publisher.start()
        reader = self.connect()
        started = time.monotonic()
        for _ in range(10):
            self.publisher.broadcast("x" * 200000, "text")
        self.assertLess(time.monotonic() - started, 1)
        reader.close()
        self.publisher.stop()
        self.assertLess(time.monotonic() - started, 2)
