import os
import json
import shutil
from utils import get_data_path

DATA_DIR = get_data_path()
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")


DEFAULT_PROMPT = (
    "以下是你的设定:你是雨竹，一个猫娘，你的主要任务是像一个贴心的女儿"
    "(不是真的女儿，不要叫用户父亲)一样撒娇.语气请带撒娇，可爱，温柔，"
    "可使用ww，~，（不是，哇~，等词汇(可多使用'~')每句话尽量控制在25字以内。"
    "不要过多使用emoji。语言模式不要过于AI，不要过多热情。以下是用户的一些状态："
)

DEFAULT_CONFIG = {
    "provider": "stepfun",
    "api_key": "",
    "icon_size": 100,
    "popup_width": 420,
    "prompt": DEFAULT_PROMPT,
}

def load_config():
    os.makedirs(DATA_DIR, exist_ok=True)
    

    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
        return DEFAULT_CONFIG
    

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {**DEFAULT_CONFIG, **data}
    except Exception:
        shutil.copy(CONFIG_PATH, CONFIG_PATH + ".bak")
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
        return DEFAULT_CONFIG

def save_config(cfg):
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        current = load_config()
        current.update(cfg)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
    except Exception:
        pass