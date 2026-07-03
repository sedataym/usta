import os


OCR_ENGINES = ["Tesseract", "EasyOCR"]  # "PaddleOCR" (uncomment when paddlepaddle is available)
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

# Map UI language codes to Tesseract/EasyOCR language codes
OCR_LANG_MAPPING = {
    "en": {"tess": "eng", "easy": "en", "paddle": "en"},
    "tr": {"tess": "tur", "easy": "tr", "paddle": "tr"},
    "ru": {"tess": "rus", "easy": "ru", "paddle": "ru"},
    "ar": {"tess": "ara", "easy": "ar", "paddle": "ar"},
    "he": {"tess": "heb", "easy": "he", "paddle": "he"},
    "de": {"tess": "deu", "easy": "de", "paddle": "de"},
    "fr": {"tess": "fra", "easy": "fr", "paddle": "fr"},
    "ja": {"tess": "jpn", "easy": "ja", "paddle": "ja"},
    "ko": {"tess": "kor", "easy": "ko", "paddle": "ko"},
    "zh": {"tess": "chi_sim", "easy": "ch_sim", "paddle": "ch"},
    "vi": {"tess": "vie", "easy": "vi", "paddle": "vi"},
    "th": {"tess": "tha", "easy": "th", "paddle": "th"},
    "es": {"tess": "spa", "easy": "es", "paddle": "es"},
}

PORTAL_ORIENTATION = -1
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "umayocr")
