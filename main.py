import time
import os
import sys
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed

# Setup path for src directory helpers and config wrapper
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

import config
import utils
import video_engine

def process_single_ayah(task_info):
    surah_num = task_info["surah_num"]
    ayah_num = task_info["ayah_num"]
    surah_data = task_info["surah_data"]
    timing_data = task_info["timing_data"]
    
    print(f"  [Worker PID: {os.getpid()}] Preparing assets for Ayah {ayah_num}...")
    assets = video_engine.prepare_ayah_assets(surah_data, timing_data, surah_num, ayah_num)
    return ayah_num, assets

if __name__ == "__main__":
    # Parse optional CLI arguments (override config.json when provided)
    parser = argparse.ArgumentParser(description="Quran Video Generator")
    parser.add_argument("--surah",      type=int, help="Surah number (1-114)")
    parser.add_argument("--start",      type=int, help="Start Ayah number")
    parser.add_argument("--end",        type=int, help="End Ayah number")
    parser.add_argument("--background", type=str, help="Background image/video path")
    args = parser.parse_args()

    # Override config values with CLI arguments when supplied
    if args.surah:      config.SURAH_NUMBER      = args.surah
    if args.start:      config.START_AYAH        = args.start
    if args.end:        config.END_AYAH          = args.end
    if args.background: config.BACKGROUND_SOURCE = args.background

    start_time = time.time()

    # 1. Pre-run Cleanup (MANDATORY)
    utils.prepare_directories(clear_temp=True)
    
    print("Loading data...")
    quran_text_data = utils.load_json_data("quran-uthmani-corrected.json")["data"]["surahs"]
    quran_timing_data = utils.load_json_data("quran_final_data.json")
    skipped_verses = utils.load_json_data("skipped_verses.json")

    all_assets = []
    
    # Handle Basmala
    if config.SURAH_NUMBER != 1 and config.SURAH_NUMBER != 9 and config.START_AYAH == 1:
        print("-" * 30); print("Generating Basmala assets...")
        basmala_assets = video_engine.prepare_ayah_assets(
            surah_data=quran_text_data[0], 
            timing_data=quran_timing_data, 
            surah_num=1, ayah_num=1,
            override_info_text=quran_text_data[config.SURAH_NUMBER - 1]["name"]
        )
        if basmala_assets:
            all_assets.append(basmala_assets)
    
    # Prepare Parallel Tasks
    tasks = []
    for ayah_num in range(config.START_AYAH, config.END_AYAH + 1):
        tasks.append({
            "surah_num": config.SURAH_NUMBER,
            "ayah_num": ayah_num,
            "surah_data": quran_text_data[config.SURAH_NUMBER - 1],
            "timing_data": quran_timing_data
        })
        
    # Parallel Asset Preparation
    results = {}
    with ProcessPoolExecutor() as executor:
        print(f"\nStarting parallel processing with {executor._max_workers} workers...")
        future_to_task = {executor.submit(process_single_ayah, task): task for task in tasks}
        for future in as_completed(future_to_task):
            ayah_num, assets = future.result()
            if assets: results[ayah_num] = assets 

    # Sequential Assembly (STRICT MODE)
    print("\nParallel processing finished. Preparing FFmpeg merge files...")
    abort_generation, failed_ayah_num = False, -1
    
    for ayah_num in range(config.START_AYAH, config.END_AYAH + 1):
        if ayah_num in results:
            print(f"Adding assets for Ayah {ayah_num}...")
            all_assets.append(results[ayah_num])
        else:
            print(f"\n[STRICT MODE] Failure encountered at Ayah {ayah_num}. Stopping generation.")
            abort_generation, failed_ayah_num = True, ayah_num
            break
        
    final_output_name = f"V6_Surah_{config.SURAH_NUMBER}_{config.START_AYAH}_to_{config.END_AYAH}"
    if abort_generation:
        last_success = failed_ayah_num - 1
        if last_success < config.START_AYAH:
            all_assets = []
        else:
            final_output_name = f"V6_Surah_{config.SURAH_NUMBER}_{config.START_AYAH}_to_{last_success}_PARTIAL"

    if all_assets:
        print("\n--- Step 1/3: Writing FFmpeg concat files ---")
        images_txt_path = os.path.join(config.IMAGE_CACHE_DIR, "images_concat.txt")
        audio_txt_path = os.path.join(config.IMAGE_CACHE_DIR, "audio_concat.txt")
        
        total_duration = 0
        with open(images_txt_path, "w", encoding="utf-8") as f_img, open(audio_txt_path, "w", encoding="utf-8") as f_aud:
            for asset in all_assets:
                # Audio concat
                # Normalize path for FFmpeg
                audio_path = os.path.abspath(asset["audio_path"]).replace("\\", "/")
                f_aud.write(f"file '{audio_path}'\n")
                
                # Image concat
                for page in asset["pages"]:
                    img_path = os.path.abspath(page["image_path"]).replace("\\", "/")
                    duration = page["duration"]
                    f_img.write(f"file '{img_path}'\n")
                    f_img.write(f"duration {duration:.3f}\n")
                    total_duration += duration
                
            # FFmpeg concat demuxer quirk: repeat the last image file without duration to ensure it holds
            if all_assets and all_assets[-1]["pages"]:
                last_img_path = os.path.abspath(all_assets[-1]["pages"][-1]["image_path"]).replace("\\", "/")
                f_img.write(f"file '{last_img_path}'\n")
        
        print("--- Step 2/3: Generating background ---")
        temp_bg_path = os.path.join(config.IMAGE_CACHE_DIR, "bg_layer.mp4")
        video_engine.create_background_video(total_duration, temp_bg_path)
        
        print("--- Step 3/3: FFmpeg native merge ---")
        out_path = utils.get_unique_filename(os.path.join(config.OUTPUT_DIR, final_output_name + ".mp4"))
        result = video_engine.merge_with_ffmpeg(temp_bg_path, images_txt_path, audio_txt_path, out_path)
        
        if result:
            print(f"\nDone! Video saved to: {out_path}")
            print(f"Total execution time: {time.time() - start_time:.2f} seconds.")
        else:
            print("\nFFmpeg merge failed. Check the error above.")
    else:
        print("No clips were created.")
