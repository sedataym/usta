"""HTTP request URLs must not appear in routine console logs."""

import io
import logging
import unittest
from unittest.mock import patch

from usta.infrastructure.logging_setup import configure_logging


class LoggingSetupTests(unittest.TestCase):
    def test_http_info_is_hidden_but_warnings_and_app_info_remain(self):
        output = io.StringIO()
        handler = logging.StreamHandler(output)
        root = logging.getLogger()
        http = logging.getLogger("httpx")
        original_level = http.level
        self.addCleanup(http.setLevel, original_level)
        with patch.object(root, "handlers", [handler]), patch.object(root, "level", logging.INFO):
            configure_logging()
            http.info("HTTP Request: GET https://example.invalid/?q=private-text")
            http.warning("Connection warning")
            logging.getLogger("usta").info("Application started")
        self.assertNotIn("private-text", output.getvalue())
        self.assertIn("Connection warning", output.getvalue())
        self.assertIn("Application started", output.getvalue())
