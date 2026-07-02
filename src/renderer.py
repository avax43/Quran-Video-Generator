import os
import base64
import hashlib
from html2image import Html2Image
import config

hti = Html2Image(
    output_path=config.IMAGE_CACHE_DIR, 
    size=config.VIDEO_SIZE,
    custom_flags=['--hide-scrollbars', '--default-background-color=00000000', '--no-sandbox', '--disable-gpu'] 
)

def create_frame_image_html(page_words, surah_data, ayah_num, override_info_text=None):
    ayah_html_content = " ".join(page_words)
    info_text = override_info_text if override_info_text else f'{surah_data["name"]} - {ayah_num}'

    page_content_hash = hashlib.md5(" ".join(page_words).encode('utf-8')).hexdigest()
    content_signature = f"{page_content_hash}-{surah_data['number']}-{ayah_num}-{info_text}-{config.TEXT_COLOR}-{config.MAIN_FONT_SIZE}"
    file_hash = hashlib.md5(content_signature.encode('utf-8')).hexdigest()
    output_file = f"frame_{file_hash}.png"
    output_path = os.path.join(config.IMAGE_CACHE_DIR, output_file)
    
    if os.path.exists(output_path):
        return output_path

    try:
        with open(config.FONT_PATH, "rb") as font_file:
            font_base64 = base64.b64encode(font_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error loading font: {e}")
        return None

    html_code = f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <style>
            @font-face {{ font-family: 'QuranFont'; src: url(data:font/ttf;base64,{font_base64}) format('truetype'); }}
            html {{ background-color: transparent; }} 
            body {{ 
                margin: 0; padding: 30px; 
                width: {config.VIDEO_WIDTH}px; height: {config.VIDEO_HEIGHT}px; 
                color: {config.TEXT_COLOR}; 
                display: flex; flex-direction: column; justify-content: center; align-items: center; 
                text-align: center; box-sizing: border-box; 
            }}
            .ayah {{ 
                font-family: 'QuranFont'; font-weight: normal; 
                font-size: {config.MAIN_FONT_SIZE}px; line-height: 2.2; 
                text-shadow: 0px 0px 10px rgba(0,0,0, 0.9);
                font-feature-settings: "kern" 1, "liga" 1, "calt" 1, "mark" 1, "mkmk" 1;
                text-rendering: optimizeLegibility; -webkit-font-smoothing: antialiased;
            }}
            .info {{ 
                font-family: 'Segoe UI', 'Arial', sans-serif; font-weight: bold;
                font-size: {config.INFO_FONT_SIZE}px; position: absolute; bottom: 12%; 
                text-shadow: 0px 0px 5px rgba(0,0,0, 0.9);
            }}
        </style>
    </head>
    <body>
        <div class="ayah">{ayah_html_content}</div>
        <div class="info">{info_text}</div>
    </body>
    </html>
    """
    hti.screenshot(html_str=html_code, save_as=output_file)
    return output_path
