import json
import os

config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.json"))

with open(config_path, "r", encoding="utf-8") as f:
    _config_data = json.load(f)

# Update globals to make config attributes accessible as config.ATTRIBUTE
globals().update(_config_data)

# Derive dependent settings
if "VIDEO_WIDTH" in _config_data and "VIDEO_HEIGHT" in _config_data:
    VIDEO_SIZE = (VIDEO_WIDTH, VIDEO_HEIGHT)
