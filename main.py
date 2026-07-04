import sys
import json
import ctypes
import os

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSignal, QUrl
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from widgets import EdgeFloatingBlock


# 工具函数

def load_config():
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"stepfun_api_key": ""}


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


class StepFunClient(QNetworkAccessManager):


    response_ready = pyqtSignal(str)

    def __init__(self, api_key, model="step-3.7-flash"):
        super().__init__()
        self._api_key = api_key
        self._model = model
        self._base_url = "https://api.stepfun.com/v1"
        self._messages = []

    def set_system_prompt(self, prompt):
        self._messages = [{"role": "system", "content": prompt}]

    def send_message(self, user_message):
        self._messages.append({"role": "user", "content": user_message})
        self._do_request()

    def _do_request(self):
        if not self._api_key:
            self.response_ready.emit("呜...还没设置 API Key 呢！去 config.json 里填一下啦笨蛋~")
            return

        body = {
            "model": self._model,
            "messages": self._messages,
            "temperature": 1,
            "stream": False
        }
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")

        req = QNetworkRequest(QUrl(f"{self._base_url}/chat/completions"))
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


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = EdgeFloatingBlock()

    config = load_config()
    ai = StepFunClient(config.get("stepfun_api_key", ""))
    ai.set_system_prompt(window.SYSTEM_PROMPT)
    window.set_ai_client(ai)

    window.show()
    sys.exit(app.exec_())