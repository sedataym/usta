import logging
from usta.resource_paths import resource_path

import gettext
import os
import locale
import unicodedata
import warnings

logger = logging.getLogger(__name__)

# Global translator object
_translator = None

_LOCALE_ENV_VARS = ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")


def _strip_invisible_characters(value):
    """Remove Unicode control/format characters from locale values."""
    return "".join(
        character
        for character in value
        if unicodedata.category(character)[0] != "C"
    )


def _normalize_locale(value):
    """Normalize a locale value for gettext lookup."""
    if not value:
        return None

    normalized = _strip_invisible_characters(value).strip()
    if not normalized:
        return None

    normalized = normalized.split(".", 1)[0].split("@", 1)[0].strip()
    if not normalized or normalized.upper() in {"C", "POSIX"}:
        return None

    return normalized


def _add_locale_candidate(candidates, seen, value):
    normalized = _normalize_locale(value)
    if normalized and normalized not in seen:
        candidates.append(normalized)
        seen.add(normalized)


def _get_locale_candidates():
    """Return locale candidates using environment variables before Python locale APIs."""
    candidates = []
    seen = set()

    for variable in _LOCALE_ENV_VARS:
        value = os.environ.get(variable)
        if not value:
            continue

        values = value.split(":") if variable == "LANGUAGE" else [value]
        for locale_value in values:
            _add_locale_candidate(candidates, seen, locale_value)

    try:
        current_locale = locale.getlocale()[0]
    except Exception:
        current_locale = None
    _add_locale_candidate(candidates, seen, current_locale)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        try:
            default_locale = locale.getdefaultlocale()[0]
        except Exception:
            default_locale = None
    _add_locale_candidate(candidates, seen, default_locale)

    return candidates

def init_i18n(locale_dir=None, domain="messages"):
    """
    Initialize internationalization.
    If locale_dir is not provided, it defaults to 'src/translations'.
    """
    global _translator
    
    if locale_dir is None:
        # Default translation directory: src/translations
        locale_dir = str(resource_path("resources/translations"))

    locale_candidates = _get_locale_candidates()

    # Load translation
    try:
        languages = locale_candidates or None
        _translator = gettext.translation(domain, locale_dir, languages=languages, fallback=True)
        _translator.install() # This installs _() into builtins
    except Exception as e:
        logger.info(f"Warning: Could not load translation for {locale_candidates}: {e}")
        # Fallback to null translation
        _translator = gettext.NullTranslations()
        _translator.install()

def _(message):
    """
    Helper function to translate a message.
    """
    if _translator is None:
        return message
    return _translator.gettext(message)
