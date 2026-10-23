import ast
import unittest
from pathlib import Path

import usta

ROOT = Path(usta.__file__).parent


class ArchitectureTests(unittest.TestCase):
    def test_core_has_no_ui_imports(self):
        for p in (ROOT / "core").rglob("*.py"):
            tree = ast.parse(p.read_text())
            for n in ast.walk(tree):
                if isinstance(n, ast.ImportFrom):
                    self.assertFalse((n.module or "").startswith("usta.ui"), str(p))

    def test_tabs_do_not_access_worker_or_mutate_panel(self):
        for p in (ROOT / "ui/tabs").glob("*.py"):
            source = p.read_text()
            self.assertNotIn("panel.worker", source, str(p))
            self.assertNotIn("panel.", source, str(p))
