# Avos (Instant OCR Translator HUD)

Avos is a high-performance, PySide6-based instant translation tool designed for Linux. It acts as a transparent HUD (Heads-Up Display) that provides **real-time subtitle translation** for games, videos, movies, and any non-selectable text on your screen.

![Avos Screenshot](docs/Screenshot_20260531_215750.png)

By "sniping" a specific area of your screen, Avos continuously monitors that region, extracts text using OCR (Optical Character Recognition), and overlays the translated text instantly, making it perfect for playing untranslated games or watching foreign media.

> **Note:** Current version is optimized for **KDE Plasma (Wayland)** using **xcb** mode. Future versions will expand compatibility.

## 🚀 Key Features

*   **Real-Time HUD Translation:** Specifically designed to provide live translations over video players and game windows.
*   **KDE & Wayland Support:** Currently runs in `xcb` mode, specifically tailored for KDE Plasma environments using native tools for region selection and capture.
*   **Sniper Mode Overlay:** Modular region selection system (currently uses `slurp`) to target subtitle areas.
*   **Modular OCR Engine Subsystem:** Dynamic multi-backend support (Tesseract & EasyOCR) for accurate text extraction.
*   **Dual-Engine Translation Subsystem:** Context-aware translations via Google Translate and DeepL (Note: DeepL is currently untested).
*   **Unix Socket IPC Broadcasting:** Real-time JSON broadcast of every translation to a local Unix socket, enabling integration with other tools (e.g., custom subtitles, logging, or OBS).
*   **Global Shortcuts & IPC Integration:** Utilizes a lightweight single-instance architecture to handle background processes and external CLI-driven shortcuts.

## 📡 External Integration (IPC)

Avos features a built-in Unix Domain Socket server that broadcasts every translation in real-time. This allows you to "pipe" translations into other applications, scripts, or overlays effortlessly.

This feature is designed for high extensibility, making it easy to integrate Avos into your existing workflow:
*   **Live Streaming:** Send translations directly to OBS or other broadcast software as a text source.
*   **Accessibility:** Integrate with text-to-speech (TTS) engines for real-time audio translation.
*   **Data Logging:** Pipe the stream to a file to create a searchable history or transcripts of your sessions.
*   **Custom Overlays:** Build your own UI or specialized subtitles that react to Avos data.

**Socket Path:** `/tmp/avos.sock`

### How to use:
You can listen to the stream using standard tools like `netcat` (nc):
```bash
nc -U /tmp/avos.sock
```

### JSON Output Format:
Every translation is sent as a single line in JSON format:
```json
{
  "original": "Hello world",
  "translated": "Merhaba dünya",
  "source": "en",
  "target": "tr",
  "engine": "Google",
  "timestamp": 1717181234.56
}
```

## 🗺️ Roadmap & Future Support

While currently focused on KDE/Linux, support for the following is planned:
- [ ] **Native Linux Packaging:** Distribution via `.deb` (Debian/Ubuntu), AUR (Arch Linux), and **Flatpak**.
- [ ] **GNOME & other Linux DEs:** Full native Wayland support without xcb.
- [ ] **Windows Support:** Integration with Windows-native capture and OCR APIs.
- [ ] **macOS Support:** Support for macOS native APIs and capture systems.

---

## 🛠️ System Requirements

Before running the application, ensure the following system packages are installed:

### Ubuntu / Debian
```bash
sudo apt update
sudo apt install tesseract-ocr slurp spectacle
```

### Arch Linux
```bash
sudo pacman -S tesseract slurp spectacle
```

---

## 📦 Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sedataym/avos.git
   cd avos
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python run.py
   ```

---

## 🛠️ Tech Stack
* **GUI:** PySide6
* **OCR:** pytesseract, easyocr
* **Translation:** deep-translator (DeepL untested)
* **Platform:** Linux (KDE optimized)
