import ctypes
import os
from datetime import datetime
import json
import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap


def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def get_data_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

data_dir = get_data_path()

def get_active_window_title():
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value if buf.value else "（无标题）"
    except Exception:
        return "（未知窗口）"


def _log_to_json(text):
    log_path = os.path.join(data_dir, "chat_log.json")
    entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content": text
    }
    try:
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
    except Exception:
        data = []
    data.append(entry)
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def capture_screen():
    screen = QApplication.primaryScreen()
    return screen.grabWindow(0)