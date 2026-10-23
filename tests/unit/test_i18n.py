import os
import unittest
from unittest import mock

from src import i18n


TRANSLATIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "src",
    "translations",
)


class I18nLocaleDetectionTests(unittest.TestCase):
    def init_with_environment(self, environment):
        with mock.patch.dict(os.environ, environment, clear=True):
            i18n.init_i18n(locale_dir=TRANSLATIONS_DIR)

    def test_lang_uk_ua_loads_ukrainian_catalog(self):
        self.init_with_environment({"LANG": "uk_UA.UTF-8"})

        self.assertEqual(i18n._("Status"), "Стан")

    def test_language_uk_loads_ukrainian_catalog(self):
        self.init_with_environment({"LANGUAGE": "uk"})

        self.assertEqual(i18n._("Translation"), "Переклад")

    def test_lang_with_zero_width_character_loads_ukrainian_catalog(self):
        self.init_with_environment({"LANG": "uk_UA.\u200bUTF-8"})

        self.assertEqual(i18n._("Status"), "Стан")

    def test_c_locale_uses_english_fallback(self):
        self.init_with_environment({"LANG": "C"})

        self.assertEqual(i18n._("Status"), "Status")


if __name__ == "__main__":
    unittest.main()
