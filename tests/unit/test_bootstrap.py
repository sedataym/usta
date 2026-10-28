import subprocess
import sys
import unittest


class BootstrapTests(unittest.TestCase):
    def test_config_import_has_no_filesystem_or_stdout_side_effects(self):
        code = """from unittest.mock import patch
with patch('os.makedirs', side_effect=AssertionError('import created directory')):
 import usta.config
"""
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
