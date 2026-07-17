from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                             QGroupBox, QLineEdit, QComboBox, QFormLayout,
                             QTextEdit,QMessageBox,QPushButton,QHBoxLayout)

from config_manager import load_config, save_config

import webbrowser


# ---------- 共用样式 ----------

GROUP_STYLE = """
    QGroupBox {
        border: 1px solid #ebedf1;
        border-radius: 8px; margin-top: 12px;
        padding: 16px 12px 12px 12px;
        font-size: 12px; color: #787d88;
    }
    QGroupBox::title {
        subcontrol-origin: margin; left: 16px; padding: 0 6px;
    }
    QLabel { color: #1e2026; }
"""

COMBO_STYLE = """
    QComboBox {
        border: 1px solid #ebedf1;
        border-radius: 6px; padding: 4px 8px;
        background: white; color: #1e2026; font-size: 12px;
    }
    QComboBox::drop-down { border: none; }
"""

INPUT_STYLE = """
    QLineEdit {
        border: 1px solid #ebedf1;
        border-radius: 6px; padding: 4px 8px;
        background: white; color: #1e2026; font-size: 12px;
    }
    QLineEdit:focus { border-color: #5078f0; }
"""

TEXT_STYLE = """
    QTextEdit {
        border: 1px solid #ebedf1;
        border-radius: 6px; padding: 4px 8px;
        background: white; color: #1e2026; font-size: 12px;
    }
    QTextEdit:focus { border-color: #5078f0; }
"""

ACCENT_BTN_STYLE = """
    QPushButton {
        background: #5078f0; color: white; border: none;
        border-radius: 6px; padding: 6px 14px;
        font-size: 12px; font-weight: bold;
    }
    QPushButton:hover { background: #6090E8; }
"""

# 厂商列表（id, 显示名）
PROVIDER_OPTIONS = [
    ("stepfun", "阶跃星辰"),
    ("bailian", "阿里百炼"),
    ("deepseek", "DeepSeek"),
]

VLM_PROVIDER_OPTIONS = [
    ("stepfun", "阶跃星辰")
]


TTS_PROVIDER_OPTIONS = [
    ("stepfun", "阶跃星辰"),
]



class BaseSettingPage(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self._build()

    def _build(self):
        raise NotImplementedError

    def save_values(self):
        return {}

    def reload_values(self, cfg):
        pass

    @staticmethod
    def _label(text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #1e2026; font-size: 12px;")
        return lbl


class AboutPage(BaseSettingPage):
    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        title = QLabel("关于 AxleTouch")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1e2026;")
        layout.addWidget(title)

        box = QGroupBox("关于")
        box.setStyleSheet(GROUP_STYLE)
        box_layout = QVBoxLayout(box)
        box_layout.addWidget(QLabel("版本：1.6.0"))
        box_layout.addWidget(QLabel("作者：Axlewire"))
        box_layout.addWidget(QLabel("许可证：GPL v3"))
        box_layout.addWidget(QLabel(" "))
        box_layout.addWidget(QLabel("仓库主页：https://github.com/baizhou830/AxleTouch"))
        box_layout.addWidget(QLabel("反馈建议：直接提 Issue"))
        layout.addWidget(box)
        layout.addStretch()


class LLMSettingPage(BaseSettingPage):
    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        title = QLabel("LLM 设置")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1e2026;")
        layout.addWidget(title)

        box = QGroupBox("模型配置")
        box.setStyleSheet(GROUP_STYLE)
        box_layout = QVBoxLayout(box)

        form = QFormLayout()
        form.setSpacing(10)

        self._provider_combo = QComboBox(self)
        self._provider_combo.setStyleSheet(COMBO_STYLE)
        for pid, pname in PROVIDER_OPTIONS:
            self._provider_combo.addItem(pname, pid)
        self._set_provider(self._config.get("provider", "stepfun"))
        self._provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        form.addRow(self._label("模型厂商:"), self._provider_combo)

        self._api_key_edit = QLineEdit(self._config.get("api_key", ""))
        self._api_key_edit.setStyleSheet(INPUT_STYLE)
        self._api_key_edit.setPlaceholderText("输入 API Key")
        form.addRow(self._label("API Key:"), self._api_key_edit)

        self._prompt_edit = QLineEdit(self._config.get("prompt", ""))
        self._prompt_edit.setStyleSheet(INPUT_STYLE)
        self._prompt_edit.setPlaceholderText("自定义 prompt")
        form.addRow(self._label("Prompt:"), self._prompt_edit)

        box_layout.addLayout(form)
        layout.addWidget(box)
        layout.addStretch()

    def _on_provider_changed(self, idx):
        pname = self._provider_combo.currentText()
        self._api_key_edit.setPlaceholderText(f"输入 {pname} API Key")

    def _set_provider(self, pid):
        idx = self._provider_combo.findData(pid)
        if idx >= 0:
            self._provider_combo.setCurrentIndex(idx)

    def save_values(self):
        return {
            "provider": self._provider_combo.currentData(),
            "api_key": self._api_key_edit.text().strip(),
            "prompt": self._prompt_edit.text().strip(),
        }

    def reload_values(self, cfg):
        self._set_provider(cfg.get("provider", "stepfun"))
        self._api_key_edit.setText(cfg.get("api_key", ""))
        self._prompt_edit.setText(cfg.get("prompt", ""))



class TTSSettingPage(BaseSettingPage):
    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        title = QLabel("TTS 设置")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1e2026;")
        layout.addWidget(title)

        box = QGroupBox("语音合成")
        box.setStyleSheet(GROUP_STYLE)
        box_layout = QVBoxLayout(box)

        form = QFormLayout()
        form.setSpacing(10)

        self._tts_provider_combo = QComboBox(self)
        self._tts_provider_combo.setStyleSheet(COMBO_STYLE)
        for pid, pname in TTS_PROVIDER_OPTIONS:
            self._tts_provider_combo.addItem(pname, pid)
        self._set_tts_provider(self._config.get("tts_provider", "stepfun"))
        form.addRow(self._label("TTS 厂商:"), self._tts_provider_combo)

        self._tts_key_edit = QLineEdit(self._config.get("tts_api_key", ""))
        self._tts_key_edit.setStyleSheet(INPUT_STYLE)
        self._tts_key_edit.setPlaceholderText("输入 StepFun TTS API Key（可留空）")
        form.addRow(self._label("TTS Key:"), self._tts_key_edit)

        self._tone_edit = QLineEdit(self._config.get("tts_tone", ""))
        self._tone_edit.setStyleSheet(INPUT_STYLE)
        self._tone_edit.setPlaceholderText("自定义音色")
        form.addRow(self._label("Tone:"), self._tone_edit)

        box_layout.addLayout(form)

        instr_label = self._label("Instruction:")
        box_layout.addWidget(instr_label)
        self._instruction_edit = QTextEdit(self._config.get("tts_instruction", ""))
        self._instruction_edit.setStyleSheet(TEXT_STYLE)
        self._instruction_edit.setFixedHeight(80)
        self._instruction_edit.setPlaceholderText("TTS 风格指令（可留空）")
        box_layout.addWidget(self._instruction_edit)

        layout.addWidget(box)
        layout.addStretch()

    def _set_tts_provider(self, pid):
        idx = self._tts_provider_combo.findData(pid)
        if idx >= 0:
            self._tts_provider_combo.setCurrentIndex(idx)

    def save_values(self):
        return {
            "tts_provider": self._tts_provider_combo.currentData(),
            "tts_api_key": self._tts_key_edit.text().strip(),
            "tts_tone": self._tone_edit.text().strip(),
            "tts_instruction": self._instruction_edit.toPlainText().strip(),
        }

    def reload_values(self, cfg):
        self._set_tts_provider(cfg.get("tts_provider", "stepfun"))
        self._tts_key_edit.setText(cfg.get("tts_api_key", ""))
        self._tone_edit.setText(cfg.get("tts_tone", ""))
        self._instruction_edit.setPlainText(cfg.get("tts_instruction", ""))



class WebSearchSettingPage(BaseSettingPage):
    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        title = QLabel("Web 搜索设置")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1e2026;")
        layout.addWidget(title)

        box = QGroupBox("Tavily 搜索")
        box.setStyleSheet(GROUP_STYLE)
        box_layout = QVBoxLayout(box)

        hint = QLabel("配置 Tavily API Key 后，AI 可在对话中调用 Web 搜索工具。留空则不启用。")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #787d88; font-size: 11px;")
        box_layout.addWidget(hint)

        form = QFormLayout()
        form.setSpacing(10)

        self._tavily_key_edit = QLineEdit(self._config.get("tavily_api_key", ""))
        self._tavily_key_edit.setStyleSheet(INPUT_STYLE)
        self._tavily_key_edit.setPlaceholderText("输入 Tavily API Key（可留空）")
        form.addRow(self._label("Tavily Key:"), self._tavily_key_edit)

        box_layout.addLayout(form)
        layout.addWidget(box)
        layout.addStretch()

    def save_values(self):
        return {
            "tavily_api_key": self._tavily_key_edit.text().strip(),
        }

    def reload_values(self, cfg):
        self._tavily_key_edit.setText(cfg.get("tavily_api_key", ""))


class VisionSettingPage(BaseSettingPage):
    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        title = QLabel("识图 API 设置")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1e2026;")
        layout.addWidget(title)

        box = QGroupBox("图像识别")
        box.setStyleSheet(GROUP_STYLE)
        box_layout = QVBoxLayout(box)

        hint = QLabel("配置识图 API，图像识别将使用此处配置。")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #787d88; font-size: 11px;")
        box_layout.addWidget(hint)

        form = QFormLayout()
        form.setSpacing(10)

        self._vision_provider_combo = QComboBox(self)
        self._vision_provider_combo.setStyleSheet(COMBO_STYLE)
        for pid, pname in VLM_PROVIDER_OPTIONS:
            self._vision_provider_combo.addItem(pname, pid)
        self._set_vision_provider(self._config.get("vision_provider", "stepfun"))
        form.addRow(self._label("模型厂商:"), self._vision_provider_combo)

        self._vision_key_edit = QLineEdit(self._config.get("vision_api_key", ""))
        self._vision_key_edit.setStyleSheet(INPUT_STYLE)
        self._vision_key_edit.setPlaceholderText("输入API Key")
        form.addRow(self._label("API Key:"), self._vision_key_edit)

        box_layout.addLayout(form)
        layout.addWidget(box)
        layout.addStretch()

    def _set_vision_provider(self, pid):
        idx = self._vision_provider_combo.findData(pid)
        if idx >= 0:
            self._vision_provider_combo.setCurrentIndex(idx)

    def save_values(self):
        return {
            "vision_provider": self._vision_provider_combo.currentData(),
            "vision_api_key": self._vision_key_edit.text().strip(),
        }

    def reload_values(self, cfg):
        self._set_vision_provider(cfg.get("vision_provider", "stepfun"))
        self._vision_key_edit.setText(cfg.get("vision_api_key", ""))




class SettingPage(BaseSettingPage):
    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(12)

        title = QLabel("通用设置")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #1e2026;")
        layout.addWidget(title)

        box = QGroupBox("通用")
        box.setStyleSheet(GROUP_STYLE)
        box_layout = QVBoxLayout(box)

        hint = QLabel("在此配置部分通用设置。")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #787d88; font-size: 11px;")
        box_layout.addWidget(hint)

        form = QFormLayout()
        form.setSpacing(10)


        form.addWidget(self._label("尝试使用 QVariantAnimation 步进优化替代 pyqtProperty 驱动（实验性）："))
        self.startup_btn = QPushButton("未启用")
        self.startup_btn.setStyleSheet(ACCENT_BTN_STYLE)
        self.startup_btn.clicked.connect(self.startup)
        form.addWidget(self.startup_btn)

        box_layout.addLayout(form)
        layout.addWidget(box)
        layout.addStretch()

    def startup(self):
        message = QMessageBox.question(None, "确认启用",
                                     f"确定要启用该实验选项吗？\n若发生错误，目前的程序无法正确地fallback至 pyqtProperty 驱动，进而导致崩溃或异常。\n且 QVariantAnimation 所带来的优化极其有限。",
                                     QMessageBox.Yes | QMessageBox.No)
        if message == QMessageBox.Yes:
            message1 = QMessageBox.question(None, "再次警告",
                                     f"此实验性设置项可能会带来风险。可能导致 QVariantAnimation 与现有动画冲突，界面可能出现卡死或异常。",
                                     QMessageBox.Yes | QMessageBox.No)
            if message1 == QMessageBox.Yes:
                url = "https://www.bilibili.com/video/BV1UT42167xb"
                webbrowser.open(url)