import sys
import json
import ctypes
import os

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal, QUrl

from utils import get_base_path, get_data_path
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from widgets import EdgeFloatingBlock


# 厂商配置
PROVIDER_CONFIGS = {
    "stepfun": {
        "name": "阶跃星辰",
        "base_url": "https://api.stepfun.com/v1",
        "default_model": "step-3.7-flash",
    },
    "bailian": {
        "name": "阿里百炼",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-turbo",
    },
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
    },
}


# 工具函数

def load_config():
    cfg_path = os.path.join(get_data_path(), "config.toml")
    try:
        import tomllib
        with open(cfg_path, "rb") as f:
            data = tomllib.load(f)
            provider = data.get("provider", "stepfun")
            if provider not in PROVIDER_CONFIGS:
                provider = "stepfun"
            return {
                "provider": provider,
                "api_key": data.get("api_key", ""),
                "icon_size": data.get("icon_size", 100),
                "popup_width": data.get("popup_width", 420),
            }
    except FileNotFoundError:
        default = {"provider": "stepfun", "api_key": "", "icon_size": 100, "popup_width": 420}
        _save_config(default)
        return default
    except Exception:
        return {"provider": "stepfun", "api_key": "", "icon_size": 100, "popup_width": 420}


def _save_config(cfg):
    cfg_path = os.path.join(get_data_path(), "config.toml")
    try:
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write(f'provider = "{cfg.get("provider", "stepfun")}"\n')
            f.write(f'api_key = "{cfg.get("api_key", "")}"\n')
            f.write(f'icon_size = {cfg.get("icon_size", 100)}\n')
            f.write(f'popup_width = {cfg.get("popup_width", 420)}\n')
    except Exception:
        pass


def get_active_window_title():
    """获取当前活动窗口标题"""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value if buf.value else "（无标题）"
    except Exception:
        return "（未知窗口）"


class AIClient(QNetworkAccessManager):


    response_ready = pyqtSignal(str)

    def __init__(self, provider, api_key):
        super().__init__()
        self._provider = provider
        self._api_key = api_key
        self._messages = []

    @property
    def _cfg(self):
        return PROVIDER_CONFIGS.get(self._provider, PROVIDER_CONFIGS["stepfun"])

    def set_system_prompt(self, prompt):
        self._messages = [{"role": "system", "content": prompt}]

    def update(self, provider, api_key):
        self._provider = provider
        self._api_key = api_key
        self._messages = [self._messages[0]] if self._messages else []

    def send_message(self, user_message):
        self._messages.append({"role": "user", "content": user_message})
        self._do_request()

    def _do_request(self):
        if not self._api_key:
            self.response_ready.emit("呜...还没设置 API Key 呢！去设置里填一下啦笨蛋~")
            return

        body = {
            "model": self._cfg["default_model"],
            "messages": self._messages,
            "temperature": 1,
            "stream": False
        }
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")

        req = QNetworkRequest(QUrl(f"{self._cfg['base_url']}/chat/completions"))
        req.setHeader(QNetworkRequest.ContentTypeHeader, "application/json")
        req.setRawHeader(b"Authorization", f"Bearer {self._api_key}".encode())
        reply = self.post(req, raw)
        reply.finished.connect(lambda r=reply: self._on_reply(r))

    def _on_reply(self, reply):
        try:
            if reply.error() != QNetworkReply.NoError:
                self.response_ready.emit(f"呜...网络错误: {reply.errorString()}")
                reply.deleteLater()
                return

            raw = reply.readAll().data().decode()
            data = json.loads(raw)
            content = data["choices"][0]["message"]["content"]
            self._messages.append({"role": "assistant", "content": content})
            self.response_ready.emit(content)
        except Exception as e:
            self.response_ready.emit(f"呜...解析失败: {e}")
        finally:
            reply.deleteLater()


def main():
    app = QApplication(sys.argv)

    window = EdgeFloatingBlock()

    config = load_config()
    ai = AIClient(config.get("provider", "stepfun"), config.get("api_key", ""))
    ai.set_system_prompt(window.SYSTEM_PROMPT)
    window.set_ai_client(ai, config)

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()