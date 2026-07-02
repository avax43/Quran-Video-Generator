import os
import shutil
import json
import requests
from pathlib import Path
from PIL import ImageFont
import config

def prepare_directories(clear_temp=False):
    for d in [config.OUTPUT_DIR, config.AUDIO_CACHE_DIR, config.IMAGE_CACHE_DIR, config.BACKGROUNDS_DIR]:
        os.makedirs(d, exist_ok=True)
    
    if clear_temp:
        print(f"Clearing image cache in {config.IMAGE_CACHE_DIR}...")
        for filename in os.listdir(config.IMAGE_CACHE_DIR):
            file_path = os.path.join(config.IMAGE_CACHE_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

def load_json_data(filename):
    path = os.path.join(config.DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def download_audio(surah, ayah):
    url = f"https://everyayah.com/data/Alafasy_128kbps/{str(surah).zfill(3)}{str(ayah).zfill(3)}.mp3"
    filepath = os.path.join(config.AUDIO_CACHE_DIR, f"{surah}_{ayah}.mp3")
    
    if not os.path.exists(filepath):
        print(f"Downloading audio for {surah}:{ayah}...")
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status() 
            with open(filepath, 'wb') as f: f.write(r.content)
        except Exception as e:
            print(f"Error downloading audio: {e}")
            return None

    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        return filepath
    return None

def clean_ayah_text(text, surah_num, ayah_num):
    if surah_num != 1 and ayah_num == 1 and text.startswith(config.BASMALA_TEXT):
        text = text.replace(config.BASMALA_TEXT, "").strip()
    
    replacements = {
        '\u0657': '\u064B', '\u065E': '\u064C', '\u0656': '\u064D',
        '\u08F0': '\u064B', '\u08F1': '\u064C', '\u08F2': '\u064D',
        '\u0671': '\u0627', 
    }

    for original, replacement in replacements.items():
        text = text.replace(original, replacement)
        
    for mark in config.STOP_MARKS:
        text = text.replace(mark, "")

    return " ".join(text.split())

def paginate_text(words_list, font_path, font_size, max_width, max_lines_per_page=1):
    font = ImageFont.truetype(font_path, font_size)
    def get_text_width(text):
        try: return font.getlength(text)
        except: return font.getsize(text)[0]

    pages, current_page_words, current_line_words, line_count = [], [], [], 1
    for word in words_list:
        test_line_words = current_line_words + [word]
        if get_text_width(" ".join(test_line_words)) > max_width:
            current_page_words.extend(current_line_words)
            current_line_words = [word]
            line_count += 1
            if line_count > max_lines_per_page:
                pages.append(current_page_words)
                current_page_words, line_count = [], 1
        else:
            current_line_words.append(word)
    current_page_words.extend(current_line_words)
    if current_page_words: pages.append(current_page_words)
    
    return pages

def get_unique_filename(filepath):
    if not os.path.exists(filepath):
        return filepath
    path = Path(filepath)
    name, ext, parent = path.stem, path.suffix, path.parent
    counter = 1
    while True:
        new_path = parent / f"{name} ({counter}){ext}"
        if not new_path.exists(): return str(new_path)
        counter += 1
