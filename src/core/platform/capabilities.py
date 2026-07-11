import os


OCR_ENGINES = ["RapidOCR","Tesseract", "EasyOCR"]  # "PaddleOCR" (uncomment when paddlepaddle is available)
TRANSLATION_ENGINES = ["Google", "DeepL"]
SCREENSHOT_ENGINES = ["Portal", "Spectacle"]

LANGUAGES = {
    "Auto": "auto",
    "English": "en",
    "Turkish": "tr",
    "German": "de",
    "French": "fr",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese": "zh",
    "Russian": "ru",
    "Arabic": "ar",
    "Hebrew": "he",
    "Vietnamese": "vi",
    "Thai": "th",
    "Spanish": "es",
}

# Map UI language codes to OCR engine language codes
OCR_LANG_MAPPING = {
    "en": {"tess": "eng", "easy": "en", "paddle": "en", "rapid": "en"},
    "tr": {"tess": "tur", "easy": "tr", "paddle": "tr", "rapid": "tr"},
    "ru": {"tess": "rus", "easy": "ru", "paddle": "ru", "rapid": "ru"},
    "ar": {"tess": "ara", "easy": "ar", "paddle": "ar", "rapid": "ar"},
    "he": {"tess": "heb", "easy": "he", "paddle": "he", "rapid": "he"},
    "de": {"tess": "deu", "easy": "de", "paddle": "de", "rapid": "de"},
    "fr": {"tess": "fra", "easy": "fr", "paddle": "fr", "rapid": "fr"},
    "ja": {"tess": "jpn", "easy": "ja", "paddle": "ja", "rapid": "japan"},
    "ko": {"tess": "kor", "easy": "ko", "paddle": "ko", "rapid": "korean"},
    "zh": {"tess": "chi_sim", "easy": "ch_sim", "paddle": "ch", "rapid": "ch"},
    "vi": {"tess": "vie", "easy": "vi", "paddle": "vi", "rapid": "vi"},
    "th": {"tess": "tha", "easy": "th", "paddle": "th", "rapid": "th"},
    "es": {"tess": "spa", "easy": "es", "paddle": "es", "rapid": "es"},
}

PORTAL_ORIENTATION = -1
SETTINGS_TOPMOST_HOTKEY = "<shift>+<alt>+m"
TEMPORARY_REGION_HOTKEY = "<shift>+<alt>+r"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "usta")
