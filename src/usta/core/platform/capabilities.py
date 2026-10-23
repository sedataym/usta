import os


OCR_ENGINES = ["RapidOCR","Tesseract", "EasyOCR"]  # "PaddleOCR" (uncomment when paddlepaddle is available)
TRANSLATION_ENGINES = ["Google", "DeepL"]
SCREENSHOT_ENGINES = ["Portal", "Spectacle"]

LANGUAGES = {
    "Auto": {
        "code": "auto",
        "google": {"source": "auto", "target": "auto"},
        "deepl": {"source": None, "target": None},
    },
    "English": {
        "code": "en",
        "google": {"source": "en", "target": "en"},
        "deepl": {"source": "en", "target": "en-US"},
    },
    "Turkish": {
        "code": "tr",
        "google": {"source": "tr", "target": "tr"},
        "deepl": {"source": "tr", "target": "tr"},
    },
    "German": {
        "code": "de",
        "google": {"source": "de", "target": "de"},
        "deepl": {"source": "de", "target": "de"},
    },
    "French": {
        "code": "fr",
        "google": {"source": "fr", "target": "fr"},
        "deepl": {"source": "fr", "target": "fr"},
    },
    "Japanese": {
        "code": "ja",
        "google": {"source": "ja", "target": "ja"},
        "deepl": {"source": "ja", "target": "ja"},
    },
    "Korean": {
        "code": "ko",
        "google": {"source": "ko", "target": "ko"},
        "deepl": {"source": "ko", "target": "ko"},
    },
    "Chinese": {
        "code": "zh",
        "google": {"source": "zh", "target": "zh"},
        "deepl": {"source": "zh", "target": "zh"},
    },
    "Russian": {
        "code": "ru",
        "google": {"source": "ru", "target": "ru"},
        "deepl": {"source": "ru", "target": "ru"},
    },
    "Arabic": {
        "code": "ar",
        "google": {"source": "ar", "target": "ar"},
        "deepl": {"source": "ar", "target": "ar"},
    },
    "Hebrew": {
        "code": "he",
        "google": {"source": "he", "target": "he"},
        "deepl": {"source": "he", "target": "he"},
    },
    "Vietnamese": {
        "code": "vi",
        "google": {"source": "vi", "target": "vi"},
        "deepl": {"source": "vi", "target": "vi"},
    },
    "Thai": {
        "code": "th",
        "google": {"source": "th", "target": "th"},
        "deepl": {"source": "th", "target": "th"},
    },
    "Spanish": {
        "code": "es",
        "google": {"source": "es", "target": "es"},
        "deepl": {"source": "es", "target": "es"},
    },
    "Portuguese (Brazil)": {
        "code": "pt-BR",
        "google": {"source": "pt", "target": "pt"},
        "deepl": {"source": "PT", "target": "PT-BR"},
    },
    "Ukrainian": {
        "code": "uk",
        "google": {"source": "uk", "target": "uk"},
        "deepl": {"source": "uk", "target": "uk"},
    },
}

# Map UI language codes to OCR engine language codes
OCR_LANG_MAPPING = {
    "en": {"tess": "eng", "easy": "en", "paddle": "en", "rapid": "en"},
    "tr": {"tess": "tur", "easy": "tr", "paddle": "tr", "rapid": "latin"},
    "ru": {"tess": "rus", "easy": "ru", "paddle": "ru", "rapid": "cyrillic"},
    "ar": {"tess": "ara", "easy": "ar", "paddle": "ar", "rapid": "arabic"},
    "he": {"tess": "heb", "easy": "he", "paddle": "he", "rapid": "en"},
    "de": {"tess": "deu", "easy": "de", "paddle": "de", "rapid": "latin"},
    "fr": {"tess": "fra", "easy": "fr", "paddle": "fr", "rapid": "latin"},
    "ja": {"tess": "jpn", "easy": "ja", "paddle": "ja", "rapid": "japan"},
    "ko": {"tess": "kor", "easy": "ko", "paddle": "ko", "rapid": "korean"},
    "zh": {"tess": "chi_sim", "easy": "ch_sim", "paddle": "ch", "rapid": "ch"},
    "vi": {"tess": "vie", "easy": "vi", "paddle": "vi", "rapid": "latin"},
    "th": {"tess": "tha", "easy": "th", "paddle": "th", "rapid": "th"},
    "es": {"tess": "spa", "easy": "es", "paddle": "es", "rapid": "latin"},
    "pt-BR": {"tess": "por", "easy": "pt", "paddle": "pt", "rapid": "latin"},
    "uk": {"tess": "ukr", "easy": "uk", "paddle": "uk", "rapid": "cyrillic"},
}

PORTAL_ORIENTATION = -1
SETTINGS_TOPMOST_HOTKEY = "<shift>+<alt>+m"
TEMPORARY_REGION_HOTKEY = "<shift>+<alt>+r"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "usta")
