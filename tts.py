from PyQt5.QtCore import QThread, pyqtSignal
import requests
from config_manager import load_config 
TTS_URL = "https://api.stepfun.com/step_plan/v1/audio/speech"
TTS_MODEL = "stepaudio-2.5-tts"
D_TTS_VOICE = "ruanmengnvsheng"

TTS_MAX_CHARS = 1000

config = load_config()
TTS_VOICE  = config.get("tts_tone",D_TTS_VOICE)



class TTSThread(QThread):

    audio_ready = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_key, text):
        super().__init__()
        self.api_key = api_key
        self.text = text

    def run(self):
        if not self.api_key:
            self.error_occurred.emit("未配置 TTS API Key")
            return
        if not self.text or not self.text.strip():
            self.error_occurred.emit("TTS 文本为空")
            return

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": TTS_MODEL,
            "input": self.text[:TTS_MAX_CHARS],
            "voice": TTS_VOICE,
            "response_format": "wav",
            "instruction": "用中性、柔软、带着慵懒和微微气声的嗓音说话，像一位清冷又温柔的年轻女性，不要把声音往粗壮的男声方向合成。音色不要像夹的一样、"
        }
        try:
            response = requests.post(
                TTS_URL, json=payload, headers=headers, timeout=30
            )
            response.raise_for_status()
            audio_data = response.content
            if not audio_data:
                self.error_occurred.emit("TTS 返回空音频")
                return
            self.audio_ready.emit(audio_data)
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "?"
            self.error_occurred.emit(f"TTS 请求失败 (HTTP {status})")
        except requests.exceptions.Timeout:
            self.error_occurred.emit("TTS 请求超时")
        except Exception as e:
            self.error_occurred.emit(str(e))
