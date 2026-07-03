# Quran Video Generator

A Python tool that generates vertical videos (720x1280) of Quranic verses. It overlays Arabic Uthmani text with accurate timing and syncs it with audio recitations.

## How it works

- **Rendering**: We use `html2image` (headless Chrome) to render the Arabic text. This handles complex ligatures and diacritics much better than standard Python libraries like Pillow.
- **Sync**: The script uses word-level timing data to perfectly sync the text pagination with the audio. If timing data is missing for a verse, it falls back to a proportional time distribution.
- **Video Engine**: Instead of relying on `MoviePy` for the final composition (which is slow and sometimes drops audio sync), the project uses native `FFmpeg` to concatenate frames and audio streams. This makes the generation process extremely fast.
- **Backgrounds**: The tool supports applying a slow Ken Burns zoom effect to static background images, or you can pass a looping video background.

## Project Structure

```text
gen/
├── src/
│   ├── config.py         # Handles loading the config.json file
│   ├── renderer.py       # Responsible for rendering HTML to transparent PNGs
│   ├── utils.py          # Helper functions for downloading audio and formatting text
│   └── video_engine.py   # Handles FFmpeg and background video logic
├── main.py               # The main entry point
└── config.json           # Your configuration settings
```

## Setup

1. **Requirements**: 
   - Python 3.11 or higher
   - FFmpeg installed and added to your system PATH
   - Google Chrome or Chromium (needed for `html2image`)

### ⚙️ Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/quran-video-generator.git
   cd quran-video-generator
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Edit the `config.json` file in the root directory to choose the Surah, Ayah range, and background:

```json
{
  "SURAH_NUMBER": 108,
  "START_AYAH": 1,
  "END_AYAH": 3,
  "VIDEO_WIDTH": 720,
  "VIDEO_HEIGHT": 1280,
  "FPS": 24,
  "BACKGROUND_SOURCE": "assets/backgrounds/background4.png"
}
```

Run the main script:
```bash
python main.py
```

The output will be saved in the `output/` folder.

## Credits

- **Word Timing Data**: Sourced from the [quran-align](https://github.com/cpfair/quran-align) repository by [@cpfair](https://github.com/cpfair), licensed under the MIT License.
