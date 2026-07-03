# Quran Video Generator

A Python tool that generates videos of Quranic verses with accurate timing and syncs it with audio recitations.

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
├── assets/
│   ├── backgrounds/      # Put your background images here
│   ├── data/             # Quran text and timing JSON files
│   └── fonts/
├── main.py               # The main entry point
└── config.json           # Your configuration settings
```

---

## Option A: Use via GitHub Actions (no installation required)

This is the easiest way to generate a video without installing anything on your machine.

1. **Fork** this repository to your own GitHub account.
2. Go to the **Actions** tab in your fork.
3. Click on **"Quran Video Generator"** in the left sidebar.
4. Click **"Run workflow"** and fill in the inputs:
   - **Surah number** (e.g. `108`)
   - **Start Ayah** and **End Ayah** (e.g. `1` and `3`)
   - **Background filename** — just the filename of an image in `assets/backgrounds/` (e.g. `background4.png`)
5. Click the green **"Run workflow"** button.
6. Once the workflow finishes, click on the completed run and download the video from the **Artifacts** section at the bottom.

---

## Option B: Run locally (for developers)

### Requirements

- Python 3.11 or higher
- FFmpeg installed and added to your system PATH
- Google Chrome or Chromium (needed for `html2image`)

### Installation

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

### Usage

**Option 1 — Edit `config.json` and run:**
```bash
python main.py
```

**Option 2 — Pass arguments directly on the command line:**
```bash
python main.py --surah 1 --start 1 --end 7 --background background4.png
```

CLI arguments always override `config.json` values. The `--background` flag accepts either a bare filename (looks inside `assets/backgrounds/` automatically) or a full path.

The output will be saved in the `output/` folder.

---

## Credits

- **Word Timing Data**: Sourced from the [quran-align](https://github.com/cpfair/quran-align) repository by [@cpfair](https://github.com/cpfair), licensed under the MIT License.
