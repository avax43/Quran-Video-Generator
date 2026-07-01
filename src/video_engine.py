import os
import uuid
import subprocess
import numpy as np
from PIL import Image, ImageOps
from moviepy.editor import (
    AudioFileClip, CompositeVideoClip, concatenate_videoclips, 
    ImageClip, VideoFileClip, CompositeAudioClip, ColorClip
)
from moviepy.video.fx.all import crop, resize
import config
import utils
import renderer

def process_background_image(image_path, target_size):
    if not os.path.exists(image_path):
        temp_bg_path = os.path.join(config.IMAGE_CACHE_DIR, f"missing_bg_{uuid.uuid4().hex}.jpg")
        Image.new('RGB', target_size, color='black').save(temp_bg_path)
        return temp_bg_path

    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB': img = img.convert('RGB')
            processed_img = ImageOps.fit(img, target_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            temp_bg_path = os.path.join(config.IMAGE_CACHE_DIR, f"processed_bg_{uuid.uuid4().hex}.jpg")
            processed_img.save(temp_bg_path, quality=95)
            return temp_bg_path
    except Exception as e:
        print(f"Error processing background image: {e}")
        return image_path

def resize_background_clip(clip, target_size):
    target_w, target_h = target_size
    clip_w, clip_h = clip.size
    target_ratio, clip_ratio = target_w / target_h, clip_w / clip_h

    if clip_ratio > target_ratio:
        resized_clip = clip.fx(resize, height=target_h)
        new_w = int(target_h * clip_ratio)
        x_start = (new_w - target_w) / 2
        return resized_clip.fx(crop, x1=x_start, y1=0, x2=x_start+target_w, y2=target_h)
    else:
        resized_clip = clip.fx(resize, width=target_w)
        new_h = int(target_w / clip_ratio)
        y_start = (new_h - target_h) / 2
        return resized_clip.fx(crop, x1=0, y1=y_start, x2=target_w, y2=y_start+target_h)

def apply_ken_burns_effect(img_path, duration, target_size):
    img_clip = ImageClip(img_path).set_duration(duration)
    w_target, h_target = target_size

    def transform(get_frame, t):
        img_pil = Image.fromarray(get_frame(t))
        scale = 1 + (config.ZOOM_SPEED * t)
        cw, ch = w_target / scale, h_target / scale
        left, top = (w_target - cw) / 2, (h_target - ch) / 2
        return np.array(img_pil.resize((w_target, h_target), box=(left, top, left+cw, top+ch), resample=Image.Resampling.BICUBIC))

    return img_clip.fl(transform)

def prepare_ayah_assets(surah_data, timing_data, surah_num, ayah_num, override_info_text=None):
    try:
        raw_text = surah_data["ayahs"][ayah_num - 1]["text"].replace('\uFEFF', '')
        clean_text = utils.clean_ayah_text(raw_text, surah_num, ayah_num)
        
        # Check if timing data exists for this specific ayah
        str_surah = str(surah_num)
        str_ayah = str(ayah_num)
        if str_surah in timing_data and str_ayah in timing_data[str_surah]:
            timings = timing_data[str_surah][str_ayah]
            has_timing = True
        else:
            has_timing = False
            timings = []
    except Exception as e: 
        print(f"Error parsing data for Ayah {ayah_num}: {e}")
        return None
    
    audio_path = utils.download_audio(surah_num, ayah_num)
    if not audio_path: return None
    
    # Get audio duration
    with AudioFileClip(audio_path) as audio: 
        audio_duration = audio.duration
    
    pages = utils.paginate_text(clean_text.split(), config.FONT_PATH, config.MAIN_FONT_SIZE, config.VIDEO_WIDTH * 0.9)
    pages_data, processed_words = [], 0
    duration_per_page = audio_duration / max(len(pages), 1)

    for i, page_words in enumerate(pages):
        if has_timing:
            try:
                start_ms = timings[processed_words]['start_ms']
                # Try to get the end of the last word in this page, capped at the length of timings
                end_index = min(processed_words + len(page_words) - 1, len(timings)-1)
                end_ms = timings[end_index]['end_ms']
                duration = (end_ms - start_ms) / 1000.0
            except: 
                duration = duration_per_page
        else:
            # Fallback for skipped verses
            duration = duration_per_page
            
        img_path = renderer.create_frame_image_html(page_words, surah_data, ayah_num, override_info_text)
        pages_data.append({"image_path": img_path, "duration": duration})
        processed_words += len(page_words)

    # Sync fix: Ensure total image duration matches audio exactly
    total_img_duration = sum(p["duration"] for p in pages_data)
    if total_img_duration > 0 and audio_duration > 0:
        diff = audio_duration - total_img_duration
        # Apply the difference to the last page (it's usually padding)
        pages_data[-1]["duration"] = max(0.01, pages_data[-1]["duration"] + diff)

    return {"audio_path": audio_path, "pages": pages_data, "audio_duration": audio_duration}

def create_background_video(duration, output_path):
    """Export the background as a standalone video file for FFmpeg merging."""
    w, h = config.VIDEO_SIZE
    
    if config.BACKGROUND_SOURCE.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
        if os.path.exists(config.BACKGROUND_SOURCE):
            bg = resize_background_clip(VideoFileClip(config.BACKGROUND_SOURCE, audio=False), config.VIDEO_SIZE).loop(duration=duration)
        else:
            bg = ColorClip(size=config.VIDEO_SIZE, color=(0,0,0)).set_duration(duration)
    else:
        bg_path = process_background_image(config.BACKGROUND_SOURCE, config.VIDEO_SIZE)
        if config.ENABLE_ZOOM:
            bg = apply_ken_burns_effect(bg_path, duration, config.VIDEO_SIZE)
        else:
            bg = ImageClip(bg_path).set_duration(duration)
    
    bg.write_videofile(output_path, fps=config.FPS, codec="libx264", preset="ultrafast",
                       audio=False, threads=8)
    bg.close()
    return output_path

def merge_with_ffmpeg(bg_video_path, images_txt_path, audio_txt_path, output_path):
    """Use FFmpeg natively to overlay RGBA text and merge audio with perfect sync."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", images_txt_path,
        "-f", "concat", "-safe", "0", "-i", audio_txt_path,
        "-i", bg_video_path,
        "-filter_complex",
        "[0:v]format=rgba[txt];[2:v][txt]overlay=(W-w)/2:(H-h)/2:shortest=1[out]",
        "-map", "[out]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "fast",
        "-r", str(config.FPS),
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_path
    ]
    
    print(f"Running FFmpeg merge...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error: {result.stderr[-1000:]}")
        return None
    return output_path
