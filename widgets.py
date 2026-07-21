from datetime import datetime

import os
import tempfile
import winsound
from pathlib import Path
from config_manager import load_config
import base64

from schedule import Poller
from tts import TTSThread

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QLineEdit, QPushButton, QLabel, QApplication,
                              QMenu, QAction, QDialog, QStackedWidget,
                              QProgressBar, QGridLayout, QListWidget,
                              QListWidgetItem, QComboBox, QGroupBox,
                              QInputDialog, QMessageBox)
from PyQt5.QtCore import (Qt, QPoint, QRect, QRectF, QPropertyAnimation,
                           QEasingCurve, QTimer, pyqtSignal, pyqtProperty,
                           QElapsedTimer, QBuffer)
from PyQt5.QtGui import (QPainter, QBrush, QColor, QPen, QPainterPath,
                          QRegion, QCursor, QFontMetrics, QPixmap, QFont)

from tools import _log_to_json, get_base_path, capture_screen
from setting import (AboutPage, LLMSettingPage, TTSSettingPage,
                     WebSearchSettingPage, VisionSettingPage,SettingPage)
from config_manager import load_config, save_config, load_foods, save_foods
from AIclient import AIClient


current_dir = get_base_path()


image_path = os.path.join(current_dir, "assets", "image.svg")

class ContentBar(QWidget):

    def __init__(self, parent_floating):
        super().__init__()
        self._parent = parent_floating
        self._progress = 0.0
        self._elapsed = QElapsedTimer()
        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(30)
        self._progress_timer.timeout.connect(self._tick_progress)
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedHeight(63)
        self.setFixedWidth(120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("""
            QLabel {
                color: #333;
                font-size: 16px;
                background: transparent;
            }
        """)
        self._label.setWordWrap(False)
        layout.addWidget(self._label)

    def show_content(self, text):
        self._label.setText(text)
        self._adjust_width(text)
        self._update_position()
        self._progress = 1.0
        self._elapsed.start()
        self._progress_timer.start()
        self._show_animated()
        show_time = min(len(text) + 1, 25)
        show_time = max(show_time, 3)
        QTimer.singleShot(show_time*1000, self._hide_animated)

    def _tick_progress(self):
        elapsed_ms = self._elapsed.elapsed()
        self._progress = max(0.0, 1.0 - elapsed_ms / 5000)
        self.update()
        if self._progress <= 0.0:
            self._progress_timer.stop()

    def _final_pos(self):
        fx = self._parent.x()
        fy = self._parent.y()
        fw = self._parent.width()
        pw = self.width()
        ph = self.height()

        screen = QApplication.primaryScreen().geometry()
        sw = screen.width()

        edge = self._parent._edge_side
        if edge == 'left':
            px = fx
        elif edge == 'right':
            px = fx + fw - pw
        else:
            px = fx + fw // 2 - pw // 2

        if px < 0:
            px = 0
        elif px + pw > sw:
            px = sw - pw

        py = fy - ph - 6
        if py < 0:
            py = fy + self._parent.height() + 6

        return QPoint(px, py)

    def _show_animated(self):
        final = self._final_pos()
        start = QPoint(final.x(), self._parent.y() - self.height())

        self.setWindowOpacity(0.0)
        self.setFixedHeight(63)
        self.move(start)
        self.show()

        anim_p = QPropertyAnimation(self, b"pos")
        anim_p.setDuration(400)
        anim_p.setStartValue(start)
        anim_p.setEndValue(final)
        anim_p.setEasingCurve(QEasingCurve.OutCubic)
        anim_p.start()
        self._show_anim_p = anim_p

        anim_o = QPropertyAnimation(self, b"windowOpacity")
        anim_o.setDuration(300)
        anim_o.setStartValue(0.0)
        anim_o.setEndValue(1.0)
        anim_o.setEasingCurve(QEasingCurve.OutCubic)
        anim_o.start()
        self._show_anim_o = anim_o

    def _hide_animated(self):
        self._progress_timer.stop()
        cur = self.pos()
        target = QPoint(cur.x(), self._parent.y() - self.height())

        anim_p = QPropertyAnimation(self, b"pos")
        anim_p.setDuration(350)
        anim_p.setStartValue(cur)
        anim_p.setEndValue(target)
        anim_p.setEasingCurve(QEasingCurve.InCubic)
        anim_p.start()
        self._hide_anim_p = anim_p

        anim_o = QPropertyAnimation(self, b"windowOpacity")
        anim_o.setDuration(300)
        anim_o.setStartValue(self.windowOpacity())
        anim_o.setEndValue(0.0)
        anim_o.setEasingCurve(QEasingCurve.InCubic)
        anim_o.finished.connect(self._after_hide)
        anim_o.start()
        self._hide_anim_o = anim_o

    def _after_hide(self):
        self.hide()
        self.setWindowOpacity(1.0)
        self._progress = 0.0

    def _adjust_width(self, text):
        fm = QFontMetrics(self._label.font())
        text_w = fm.horizontalAdvance(text)
        w = text_w + 24 * 2 + 20
        w = max(w, 120)
        self.setFixedWidth(w)

    def _update_position(self):
        self.move(self._final_pos())

    def reposition(self):
        if self.isVisible():
            self._update_position()

    def _card_rect(self):
        return QRectF(10, 10, self.width() - 20, self.height() - 20)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        card = self._card_rect()

        for i in range(4):
            offset = 6 - i * 1.5
            r = card.adjusted(-offset, -offset + 2, offset, offset + 2)
            alpha = 8 + i * 8
            painter.setBrush(QBrush(QColor(60, 65, 80, alpha)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(r, 12 + offset, 12 + offset)

        painter.setBrush(QBrush(QColor(251, 251, 253)))
        painter.setPen(QPen(QColor(230, 232, 236), 0.5))
        painter.drawRoundedRect(card, 12, 12)

        if self._progress > 0.0 and card.height() > 2:
            bar_w = card.width() * self._progress
            bar_x = card.x()
            bar_y = card.bottom() - 2.5
            painter.setBrush(QBrush(QColor(74, 144, 217, 200)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, 2.5), 1, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 12, 12)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))



class InputPopup(QWidget):

    submitted = pyqtSignal(str)
    image = pyqtSignal(str)
    not_image = pyqtSignal()
    no_vlm = pyqtSignal()

    def __init__(self, parent_floating):
        super().__init__()
        self._parent = parent_floating
        self.setAcceptDrops(True)
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedHeight(self._parent.collapsed_size)
        self.setFixedWidth(420)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._edit = QLineEdit(self)
        self._edit.setPlaceholderText("输入...")
        self._edit.setStyleSheet("""
            QLineEdit {
                background: #fbfbfd;
                border: 1px solid #e0e2e8;
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 12px;
                color: #333;
            }
            QLineEdit:focus {
                border: 1.5px solid #4a90d9;
            }
        """)
        self._edit.returnPressed.connect(self._on_submit)
        layout.addWidget(self._edit)

        self._btn = QPushButton("✓", self)
        self._btn.setFixedSize(28, 28)
        self._btn.setStyleSheet("""
            QPushButton {
                background: #4a90d9;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #3a7bc8;
            }
            QPushButton:pressed {
                background: #2e6ab5;
            }
        """)
        self._btn.clicked.connect(self._on_submit)
        layout.addWidget(self._btn)

    def _on_submit(self):
        text = self._edit.text().strip()
        if text:
            self.submitted.emit(text)
        self.hide_popup()

    def _calc_position(self):
        fx = self._parent.x()
        fy = self._parent.y()
        fh = self._parent.height()
        fw = self._parent.width()
        pw = self.width()
        ph = self.height()

        screen = QApplication.primaryScreen().geometry()
        sw = screen.width()
        sh = screen.height()

        edge = self._parent._edge_side
        if edge == 'left':
            px = fx
        elif edge == 'right':
            px = fx + fw - pw
        else:
            px = fx + fw // 2 - pw // 2

        if px < 0:
            px = 0
        elif px + pw > sw:
            px = sw - pw

        py = fy + fh + 4
        if py + ph > sh:
            py = fy - ph - 4

        return QPoint(px, py)

    def popup(self):
        pos = self._calc_position()
        self.move(pos)
        self.show()
        self._edit.setFocus()

    def reposition(self):
        if self.isVisible():
            pos = self._calc_position()
            self.move(pos)

    def hide_popup(self):
        self.hide()
        self._edit.clear()

    def apply_config(self, config):
        width = config.get("popup_width", 420)
        self.setFixedWidth(width)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()  

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return
        file_path = urls[0].toLocalFile()
        if not file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
            self.not_image.emit()
            return
        with open(file_path, "rb") as image_file:
            base64_bytes = base64.b64encode(image_file.read()).decode('utf-8')
            image_data = f"data:image/{Path(file_path).suffix[1:].lower()};base64,{base64_bytes}"
            self.image.emit(image_data)


SIDEBAR_WIDTH = 56
SIDEBAR_ITEM_H = 44
INDICATOR_H = 36
INDICATOR_W = 4


class SidebarItem(QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.selected = False
        self.hovered = False
        self.setFixedHeight(SIDEBAR_ITEM_H)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        spacer = QWidget()
        spacer.setFixedWidth(4)
        layout.addWidget(spacer)

        self.label = QLabel(text)
        self.label.setFont(QFont("Microsoft YaHei", 9))
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: #787d88;")

        layout.addWidget(self.label, stretch=1)

    def set_selected(self, sel):
        self.selected = sel
        if sel:
            self.label.setStyleSheet("color: #1e2026; font-weight: bold;")
        else:
            self.label.setStyleSheet("color: #787d88;")

    def enterEvent(self, event):
        self.hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.hovered and not self.selected:
            painter.setBrush(QBrush(QColor(241, 243, 248)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(self.rect().adjusted(6, 3, -6, -3), 8, 8)
        painter.end()
        super().paintEvent(event)


class SidebarIndicator(QWidget):
    """侧边栏滑动指示条，用 pyqtProperty 驱动动画"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._indicator_y = 16.0
        self._anim = None
        

    def get_indicator_y(self):
        return self._indicator_y

    def set_indicator_y(self, y):
        self._indicator_y = y
        self.update()

    indicator_y = pyqtProperty(float, get_indicator_y, set_indicator_y)

    def move_to(self, y):
        self._anim = QPropertyAnimation(self, b"indicator_y")
        self._anim.setDuration(200)
        self._anim.setStartValue(self._indicator_y)
        self._anim.setEndValue(float(y))
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(80, 120, 240)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(QRectF(0, self._indicator_y, INDICATOR_W, INDICATOR_H), 2, 2)


class SettingsDialog(QDialog):
    config_saved = pyqtSignal(dict)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = {**load_config(), **(config or {})}
        self._drag_pos = None
        self.setWindowTitle("AxleTouch")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(640, 620)
        self._pages = []
        self.init_ui()

    def init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(0)

        self.top_bar = QWidget()
        self.top_bar.setFixedHeight(52)
        self.top_bar.setStyleSheet("background: transparent;")
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(20, 0, 12, 0)

        title = QLabel("AxleTouch")
        title.setStyleSheet("font-size: 12pt; font-weight: bold; color: #1e2026;")
        top_layout.addWidget(title)
        top_layout.addStretch()

        self.ok_btn = QPushButton("确定")
        self.ok_btn.setFixedSize(56, 32)
        self.ok_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.ok_btn.setStyleSheet("""
            QPushButton {
                background: #5078f0; color: white; border: none;
                border-radius: 8px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background: #6090E8; }
        """)
        self.ok_btn.clicked.connect(self._on_save)
        top_layout.addWidget(self.ok_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setFixedSize(56, 32)
        self.cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #787d88;
                border: 1px solid #787d88;
                border-radius: 8px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background: #ebf0ff; }
        """)
        self.cancel_btn.clicked.connect(self._on_cancel)
        top_layout.addWidget(self.cancel_btn)

        outer.addWidget(self.top_bar)


        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: #ebedf1;")
        outer.addWidget(divider)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(SIDEBAR_WIDTH)
        self.sidebar.setStyleSheet("background: transparent;")
        side_layout = QVBoxLayout(self.sidebar)
        side_layout.setContentsMargins(0, 16, 0, 16)
        side_layout.setSpacing(2)

        self.sidebar_items = []
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")
        self._add_page("关于", AboutPage(self._config))
        self._add_page("LLM", LLMSettingPage(self._config))
        self._add_page("TTS", TTSSettingPage(self._config))
        self._add_page("搜索", WebSearchSettingPage(self._config))
        self._add_page("识图", VisionSettingPage(self._config))
        self._add_page("通用", SettingPage(self._config))
        self.sidebar.layout().addStretch()

        self.sidebar_indicator = SidebarIndicator(self.sidebar)
        self.sidebar_indicator.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.sidebar_indicator.setGeometry(0, 0, SIDEBAR_WIDTH, self.sidebar.height())

        body.addWidget(self.sidebar)

        side_div = QWidget()
        side_div.setFixedWidth(1)
        side_div.setStyleSheet("background: #ebedf1;")
        body.addWidget(side_div)

        body.addWidget(self.stack, stretch=1)
        outer.addLayout(body, stretch=1)

        self.sidebar_items[0].set_selected(True)
        self.stack.setCurrentIndex(0)
        QTimer.singleShot(50, self._init_indicator_pos)

    def _add_page(self, name, page):
        item = SidebarItem(name)
        idx = len(self.sidebar_items)
        item.mousePressEvent = lambda e, i=idx: self._on_sidebar(i)
        self.sidebar_items.append(item)
        side_layout = self.sidebar.layout()
        side_layout.addWidget(item)
        if idx < 5:
            div = QWidget()
            div.setFixedHeight(1)
            div.setFixedWidth(32)
            div.setStyleSheet("background: #e0e2e8;")
            side_layout.addWidget(div, alignment=Qt.AlignCenter)
        self.stack.addWidget(page)
        self._pages.append(page)

    def _init_indicator_pos(self):
        if self.sidebar_items:
            item = self.sidebar_items[0]
            self.sidebar_indicator._indicator_y = float(item.y() + (SIDEBAR_ITEM_H - INDICATOR_H) / 2)
            self.sidebar_indicator.update()

    def _on_sidebar(self, idx):
        if idx == self.stack.currentIndex():
            return
        for i, item in enumerate(self.sidebar_items):
            item.set_selected(i == idx)
        target = self.sidebar_items[idx]
        self.sidebar_indicator.move_to(target.y() + (SIDEBAR_ITEM_H - INDICATOR_H) / 2)
        self.stack.setCurrentIndex(idx)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 12, 12)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))
        if hasattr(self, 'sidebar_indicator'):
            self.sidebar_indicator.setGeometry(0, 0, self.sidebar.width(), self.sidebar.height())

    def _on_save(self):
        patch = {}
        for p in self._pages:
            if hasattr(p, "save_values"):
                patch.update(p.save_values())
        self._config.update(patch)
        save_config(self._config)
        self.config_saved.emit(self._config)
        self.accept()

    def _on_cancel(self):
        disk_cfg = load_config()
        for p in self._pages:
            if hasattr(p, "reload_values"):
                p.reload_values(disk_cfg)
        self.reject()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and hasattr(self, '_drag_pos') and self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def _card_rect(self):
        m = 20
        return QRectF(m, m, self.width() - m * 2, self.height() - m * 2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        card = self._card_rect()
        radius = 12

        # 阴影
        for i in range(4):
            offset = 6 - i * 1.5
            r = card.adjusted(-offset, -offset + 2, offset, offset + 2)
            alpha = 8 + i * 8
            painter.setBrush(QBrush(QColor(60, 65, 80, alpha)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(r, radius + offset, radius + offset)

        painter.setBrush(QBrush(QColor(251, 251, 253)))
        painter.setPen(QPen(QColor(230, 232, 236), 0.5))
        painter.drawRoundedRect(card, radius, radius)


        if hasattr(self, 'sidebar'):
            painter.setClipRect(card, Qt.IntersectClip)
            side_w = SIDEBAR_WIDTH
            side_rect = QRectF(card.left(), card.top(), side_w, card.height())
            painter.setBrush(QBrush(QColor(246, 247, 249)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(side_rect, radius, radius)


FULL_THRESHOLD = 80


INPUT_STYLE_FEED = """
    QLineEdit {
        border: 1px solid #ebedf1;
        border-radius: 6px; padding: 4px 8px;
        background: white; color: #1e2026; font-size: 12px;
    }
    QLineEdit:focus { border-color: #5078f0; }
"""

COMBO_STYLE_FEED = """
    QComboBox {
        border: 1px solid #ebedf1;
        border-radius: 6px; padding: 4px 8px;
        background: white; color: #1e2026; font-size: 12px;
    }
    QComboBox::drop-down { border: none; }
"""

ACCENT_BTN_STYLE_FEED = """
    QPushButton {
        background: #5078f0; color: white; border: none;
        border-radius: 6px; padding: 6px 14px;
        font-size: 12px; font-weight: bold;
    }
    QPushButton:hover { background: #6090E8; }
"""

DANGER_BTN_STYLE_FEED = """
    QPushButton {
        background: #E55; color: white; border: none;
        border-radius: 6px; padding: 6px 14px;
        font-size: 12px; font-weight: bold;
    }
    QPushButton:hover { background: #D44; }
"""

LIST_STYLE_FEED = """
    QListWidget {
        border: 1px solid #ebedf1;
        border-radius: 8px; background: white;
        font-size: 12px; color: #1e2026; padding: 4px;
    }
    QListWidget::item {
        padding: 8px 12px; border-bottom: 1px solid #ebedf1;
    }
    QListWidget::item:selected {
        background: #ebf0ff; color: #5078f0;
    }
"""


class FeedDialog(QDialog):
    food_selected = pyqtSignal(dict)

    def __init__(self, satiety_level, parent=None):
        super().__init__(parent)
        self._satiety_level = satiety_level
        self._drag_pos = None
        self.setWindowTitle("喂雨竹")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(440, 540)
        self._foods = load_foods()
        self.init_ui()

    def init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(0)

        top_bar = QWidget()
        top_bar.setFixedHeight(44)
        top_bar.setStyleSheet("background: transparent;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 12, 0)

        title = QLabel("喂雨竹")
        title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #1e2026;")
        top_layout.addWidget(title)
        top_layout.addStretch()

        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 32)
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #787d88;
                border: none; border-radius: 8px;
                font-size: 16px; font-weight: bold;
            }
            QPushButton:hover { background: #ebf0ff; color: #5078f0; }
        """)
        close_btn.clicked.connect(self.reject)
        top_layout.addWidget(close_btn)
        outer.addWidget(top_bar)

        satiety_box = QWidget()
        satiety_layout = QVBoxLayout(satiety_box)
        satiety_layout.setContentsMargins(20, 8, 20, 8)
        satiety_layout.setSpacing(8)

        satiety_label_row = QHBoxLayout()
        satiety_title = QLabel("当前饱食度")
        satiety_title.setStyleSheet("color: #1e2026; font-size: 12px;")
        satiety_label_row.addWidget(satiety_title)
        satiety_label_row.addStretch()
        self._satiety_value_label = QLabel(f"{self._satiety_level}/100")
        self._satiety_value_label.setStyleSheet(
            "color: #5078f0; font-size: 12px; font-weight: bold;")
        satiety_label_row.addWidget(self._satiety_value_label)
        satiety_layout.addLayout(satiety_label_row)

        self._satiety_bar = QProgressBar()
        self._satiety_bar.setRange(0, 100)
        self._satiety_bar.setValue(self._satiety_level)
        self._satiety_bar.setTextVisible(False)
        self._satiety_bar.setFixedHeight(8)
        self._satiety_bar.setStyleSheet("""
            QProgressBar {
                background: #ebedf1; border: none; border-radius: 4px;
            }
            QProgressBar::chunk {
                border-radius: 4px;
            }
        """)
        self._apply_satiety_bar_color()
        satiety_layout.addWidget(self._satiety_bar)

        self._status_label = QLabel(self._status_text())
        self._status_label.setStyleSheet("color: #787d88; font-size: 11px;")
        satiety_layout.addWidget(self._status_label)
        outer.addWidget(satiety_box)

        div = QWidget()
        div.setFixedHeight(1)
        div.setStyleSheet("background: #ebedf1;")
        outer.addWidget(div)

        food_box = QGroupBox("食物列表")
        food_box.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ebedf1; border-radius: 8px;
                margin-top: 12px; padding: 16px 12px 12px 12px;
                font-size: 12px; color: #787d88;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 16px; padding: 0 6px;
            }
        """)
        food_layout = QVBoxLayout(food_box)
        food_layout.setContentsMargins(12, 16, 12, 12)
        food_layout.setSpacing(10)

        add_row = QHBoxLayout()
        add_row.setSpacing(8)
        self._food_name_input = QLineEdit()
        self._food_name_input.setPlaceholderText("食物名称")
        self._food_name_input.setStyleSheet(INPUT_STYLE_FEED)
        add_row.addWidget(self._food_name_input, stretch=2)

        self._food_amount_input = QLineEdit()
        self._food_amount_input.setPlaceholderText("饱腹度")
        self._food_amount_input.setFixedWidth(60)
        self._food_amount_input.setStyleSheet(INPUT_STYLE_FEED)
        add_row.addWidget(self._food_amount_input)

        self._food_type_combo = QComboBox()
        self._food_type_combo.addItem("主食", "staple")
        self._food_type_combo.addItem("零食", "snack")
        self._food_type_combo.setFixedWidth(72)
        self._food_type_combo.setStyleSheet(COMBO_STYLE_FEED)
        add_row.addWidget(self._food_type_combo)

        add_btn = QPushButton("+ 添加")
        add_btn.setStyleSheet(ACCENT_BTN_STYLE_FEED)
        add_btn.setCursor(QCursor(Qt.PointingHandCursor))
        add_btn.clicked.connect(self._add_food)
        add_row.addWidget(add_btn)
        food_layout.addLayout(add_row)

        self._food_list = QListWidget()
        self._food_list.setStyleSheet(LIST_STYLE_FEED)
        food_layout.addWidget(self._food_list)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        feed_btn = QPushButton("投喂选中")
        feed_btn.setStyleSheet(ACCENT_BTN_STYLE_FEED)
        feed_btn.setCursor(QCursor(Qt.PointingHandCursor))
        feed_btn.clicked.connect(self._pick_selected)
        btn_row.addWidget(feed_btn)

        del_btn = QPushButton("删除")
        del_btn.setStyleSheet(DANGER_BTN_STYLE_FEED)
        del_btn.setCursor(QCursor(Qt.PointingHandCursor))
        del_btn.clicked.connect(self._remove_food)
        btn_row.addWidget(del_btn)

        btn_row.addStretch()
        food_layout.addLayout(btn_row)

        outer.addWidget(food_box, stretch=1)

        self._is_full = self._satiety_level >= FULL_THRESHOLD
        self._refresh_food_list()

    def _refresh_food_list(self):
        self._food_list.clear()
        for food in self._foods:
            type_tag = "零食" if food["type"] == "snack" else "主食"
            disabled = self._is_full and food["type"] == "staple"
            suffix = "（吃饱啦~）" if disabled else ""
            text = f"  {food['name']}    +{food['amount']} 饱食度    [{type_tag}]{suffix}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, food)
            if disabled:
                item.setForeground(QColor(192, 196, 204))
            self._food_list.addItem(item)


    def _add_food(self):
        name = self._food_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入食物名称")
            return
        if any(f["name"] == name for f in self._foods):
            QMessageBox.warning(self, "提示", f"已存在名为「{name}」的食物")
            return
        try:
            amount = int(self._food_amount_input.text().strip() or "0")
        except ValueError:
            QMessageBox.warning(self, "提示", "饱腹度需为整数")
            return
        amount = max(1, min(amount, 100))
        food_type = self._food_type_combo.currentData()
        self._foods.append({"name": name, "amount": amount, "type": food_type})
        self._persist_foods()
        self._food_name_input.clear()
        self._food_amount_input.clear()
        self._refresh_food_list()

    def _remove_food(self):
        item = self._food_list.currentItem()
        if not item:
            QMessageBox.warning(self, "提示", "请先选择一个食物")
            return
        food = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "确认删除", f"确定要删除食物「{food['name']}」吗？",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._foods = [f for f in self._foods if f["name"] != food["name"]]
            self._persist_foods()
            self._refresh_food_list()

    def _pick_selected(self):
        item = self._food_list.currentItem()
        if not item:
            QMessageBox.warning(self, "提示", "请先选择一个食物")
            return
        food = item.data(Qt.UserRole)
        if self._is_full and food["type"] == "staple":
            QMessageBox.information(self, "饱腹啦", "雨竹现在饱饱的，只吃零食哦~")
            return
        self.food_selected.emit(food)
        self.accept()

    def _persist_foods(self):
        try:
            save_foods(self._foods)
        except Exception:
            pass

    def _apply_satiety_bar_color(self):
        level = self._satiety_level
        if level >= FULL_THRESHOLD:
            color = "#67c23a"
        elif level >= 50:
            color = "#5078f0"
        elif level >= 20:
            color = "#e6a23c"
        else:
            color = "#f56c6c"
        self._satiety_bar.setStyleSheet(
            "QProgressBar { background: #ebedf1; border: none; border-radius: 4px; }"
            f"QProgressBar::chunk {{ background: {color}; border-radius: 4px; }}"
        )

    def _status_text(self):
        level = self._satiety_level
        if level >= FULL_THRESHOLD:
            return "雨竹现在饱饱的~"
        elif level >= 50:
            return "雨竹还好，有点想吃东西~"
        elif level >= 20:
            return "雨竹饿了，快喂喂她~"
        else:
            return "雨竹快饿坏了！"

    def resizeEvent(self, event):
        super().resizeEvent(event)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 12, 12)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def _card_rect(self):
        m = 20
        return QRectF(m, m, self.width() - m * 2, self.height() - m * 2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        card = self._card_rect()
        radius = 12
        for i in range(4):
            offset = 6 - i * 1.5
            r = card.adjusted(-offset, -offset + 2, offset, offset + 2)
            alpha = 8 + i * 8
            painter.setBrush(QBrush(QColor(60, 65, 80, alpha)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(r, radius + offset, radius + offset)
        painter.setBrush(QBrush(QColor(251, 251, 253)))
        painter.setPen(QPen(QColor(230, 232, 236), 0.5))
        painter.drawRoundedRect(card, radius, radius)


class EdgeFloatingBlock(QWidget):
    def __init__(self):
        super().__init__()
        self.collapsed_size = 100
        self._edge_side = 'right'
        self._animating = False

        self._press_pos = None
        self._drag_offset = None
        self._long_press_fired = False
        self._is_dragging = False
        self._long_press_timer = QTimer(self)
        self._long_press_timer.setSingleShot(True)
        self._long_press_timer.timeout.connect(self._on_long_press)

        self._input_popup = InputPopup(self)
        self._input_popup.submitted.connect(self._on_input_submitted)
        self._input_popup.not_image.connect(self._not_image)
        self._input_popup.image.connect(self._image)
        self._input_popup.no_vlm.connect(self._no_vlm)


        self._content_bar = ContentBar(self)

        pixmap = QPixmap(image_path)
        self.image = pixmap.scaled(720, 720,
                                   Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self._ai = None
        self._vision_ai = None  
        self._vision_busy = False  
        self._config = None

        self._poller = Poller(self)
        self._poller.status_ready.connect(self._on_poller_status)
        self._poller.vision_trigger.connect(self._on_poller_vision)

        self._satiety_level = 100
        self._last_satiety_notify = -1
        self._satiety_timer = QTimer(self)
        self._satiety_timer.timeout.connect(self._decrease_satiety)

        self.init_ui()

    def _decrease_satiety(self):
        if self._satiety_level > 0:
            self._satiety_level -= 1
            self._update_satiety_display(self._satiety_level)

    def _feed(self, amount):
        self._satiety_level = min(100, self._satiety_level + amount)
        self._update_satiety_display(self._satiety_level)

    def _update_satiety_display(self, level):
        thresholds = {50: "有点饿了~", 20: "好饿好饿...", 0: "饿到没力气了..."}
        if level in thresholds and self._last_satiety_notify != level:
            self._content_bar.show_content(thresholds[level])
            self._last_satiety_notify = level
        elif level not in thresholds:
            self._last_satiety_notify = -1

    def _apply_satiety_config(self):
        if not self._config:
            return
        enabled = self._config.get("satiety_enabled", False)
        try:
            interval = int(self._config.get("satiety_interval", 10))
        except (TypeError, ValueError):
            interval = 10
        self._satiety_timer.setInterval(max(1, interval) * 1000)
        if enabled and not self._satiety_timer.isActive():
            self._satiety_timer.start()
        elif not enabled and self._satiety_timer.isActive():
            self._satiety_timer.stop()

    def _apply_poller_config(self):
        if self._config:
            self._poller.update_config(self._config)

    def _on_poller_vision(self):
        self.capture()

    def _on_poller_status(self, status_text):
        if self._ai:
            if self._satiety_timer.isActive():
                satiety = self._satiety_level
                desc = self._satiety_description(satiety)
                full_status = (f"{status_text}；雨竹当前饱食度: {satiety}/100（{desc}）。"
                               f"提示：饱食度越低，雨竹越饥饿，请在回复中体现相应状态。")
            else:
                full_status = status_text
            self._ai.send_message(full_status)

    def _satiety_description(self, level):
        if level >= FULL_THRESHOLD:
            return "饱腹"
        elif level >= 50:
            return "微饿"
        elif level >= 20:
            return "饥饿"
        else:
            return "非常饥饿"

    def set_ai_client(self, client, config=None):
        self._ai = client
        self._config = config or {}
        self._ai.response_ready.connect(self._on_ai_response)
        self._apply_size_config()
        self._apply_satiety_config()
        self._apply_poller_config()


    def _apply_size_config(self):
        icon_size = self._config.get("icon_size", 100)
        self.collapsed_size = icon_size
        self.resize(icon_size, icon_size)

        pixmap = QPixmap(image_path)
        self.image = pixmap.scaled(int(icon_size * 7.2), int(icon_size * 7.2),
                                   Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self._input_popup.apply_config(self._config)

        screen = QApplication.primaryScreen().geometry()
        if self._edge_side == 'left':
            self.move(0, self.y())
        else:
            self.move(screen.width() - icon_size, self.y())


    def _on_ai_response(self, text):
        self._content_bar.show_content(text)
        print("[", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "]", "\n",
              "雨竹：", "\"", text, "\"", "\n")
        _log_to_json(text)

        tts_api_key = self._config.get("tts_api_key", "") if self._config else ""
        if tts_api_key:
            tts_text = text.replace("[web search]", "").strip()
            if tts_text:
                self._tts_thread = TTSThread(tts_api_key, tts_text)
                self._tts_thread.audio_ready.connect(self._on_tts_audio_ready)
                self._tts_thread.error_occurred.connect(self._on_tts_error)
                self._tts_thread.start()

    def _on_tts_audio_ready(self, audio_data):
        temp_path = os.path.join(tempfile.gettempdir(), "axletouch_tts.wav")
        try:
            with open(temp_path, "wb") as f:
                f.write(audio_data)
            winsound.PlaySound(temp_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        except Exception as e:
            print("TTS 播放失败:", e)

    def _on_tts_error(self, error_msg):
        print("TTS 错误:", error_msg)

    def _on_input_submitted(self, text):
        print(" -----[ user input ]----- ", "\n",
              "[", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "]", "\n",
              "\"", text, "\"","\n")
        if self._ai:
            if self._satiety_timer.isActive():
                satiety = self._satiety_level
                desc = self._satiety_description(satiety)
                full = (f"{text}\n"
                        f"（提示：你的当前饱食度: {satiety}/100（{desc}）。"
                        f"饱食度越低，雨竹越饥饿，请在回复中体现相应状态。）")
            else:
                full = text
            self._ai.send_message(full)

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        screen = QApplication.primaryScreen().geometry()
        default_size = self.collapsed_size
        self.resize(default_size, default_size)
        cy = (screen.height() - default_size) // 2
        self.move(screen.width() - default_size, cy)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

    def moveEvent(self, event):
        super().moveEvent(event)
        self._input_popup.reposition()
        self._content_bar.reposition()

    def _snap_to_edge(self):
        screen = QApplication.primaryScreen().geometry()
        center_x = self.x() + self.width() / 2
        self._edge_side = 'left' if center_x < screen.width() / 2 else 'right'

        anim = QPropertyAnimation(self, b"pos")
        anim.setDuration(200)
        anim.setEasingCurve(QEasingCurve.InOutCubic)

        cur_y = self.y()
        if self._edge_side == 'left':
            target = QPoint(0, cur_y)
        else:
            target = QPoint(screen.width() - self.width(), cur_y)

        anim.setStartValue(self.pos())
        anim.setEndValue(target)
        anim.start()

    def _on_long_press(self):
        self._long_press_fired = True
        self._is_dragging = True
        self.setCursor(QCursor(Qt.ClosedHandCursor))

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        self._press_pos = event.globalPos()
        self._drag_offset = event.globalPos() - self.pos()
        self._long_press_fired = False
        self._is_dragging = False
        self._long_press_timer.start(300)

    def mouseMoveEvent(self, event):
        if not event.buttons() & Qt.LeftButton or self._press_pos is None:
            return
        dist = (event.globalPos() - self._press_pos).manhattanLength()
        if dist > 5 and not self._long_press_fired:
            self._long_press_timer.stop()
            self._long_press_fired = True
            self._is_dragging = True
            self.setCursor(QCursor(Qt.ClosedHandCursor))

        if self._is_dragging:
            self.move(event.globalPos() - self._drag_offset)

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        self._long_press_timer.stop()

        if self._is_dragging:
            self._snap_to_edge()
        else:
            if self._input_popup.isVisible():
                self._input_popup.hide_popup()
            else:
                self._input_popup.popup()

        self._long_press_fired = False
        self._is_dragging = False
        self._press_pos = None
        self.setCursor(QCursor(Qt.ArrowCursor))

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #fbfbfd;
                border: 1px solid #e0e2e8;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 4px;
                font-size: 13px;
            }
            QMenu::item:selected {
                background: #4a90d9;
                color: white;
            }
        """)

        settings_action = QAction("关于与设置", self)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        capture_action = QAction("让雨竹看看！", self)
        capture_action.triggered.connect(self._capture)
        menu.addAction(capture_action)

        menu.addSeparator()

        feed_action = QAction("喂雨竹", self)
        feed_action.triggered.connect(self._on_feed)
        menu.addAction(feed_action)

        menu.addSeparator()

        act_action = QAction("摸摸头",self)
        act_action.triggered.connect(self._on_action)
        menu.addAction(act_action)

        menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(QApplication.quit)
        menu.addAction(exit_action)

        menu.exec_(event.globalPos())

    def _open_settings(self):
        dialog = SettingsDialog(self._config or {}, self)
        dialog.config_saved.connect(self._on_config_saved)
        dialog.exec_()

    def _resolve_vision_creds(self):
        vision_provider = self._config.get("vision_provider", "stepfun")
        vision_key = self._config.get("vision_api_key", "")
        if not vision_key:
            vision_key = self._config.get("api_key", "")
        if not vision_key:
            return None
        return vision_provider, vision_key

    def _send_to_vision(self, image_url, prompt_text):
        if self._vision_busy:
            print("识图忙碌：上一次请求尚未返回，已忽略本次图片")
            return
        creds = self._resolve_vision_creds()
        if creds is None:
            print("识图失败：未配置识图 API Key")
            self._content_bar.show_content("没有识图 API Key 哦，去设置里填一下~")
            return
        vision_provider, vision_key = creds
        _data = [
            {"type": "text", "text": prompt_text},
            {"type": "image_url", "image_url": {"url": image_url, "detail": "high"}}
        ]
        if self._vision_ai is None:
            self._vision_ai = AIClient(vision_provider, vision_key, "")
            self._vision_ai.response_ready.connect(self._on_vision_describe)
        else:
            self._vision_ai.update(vision_provider, vision_key, "")
        self._vision_ai.set_system_prompt("你是图像描述助手。请用中文客观、准确地描述图片内容，不要加入个人情感或对话语气。")
        self._vision_busy = True
        self._vision_ai.send_message(_data)

    def capture(self):
        try:
            pixmap = capture_screen()
        except Exception:
            print("截图失败：无法获取屏幕图像")
            return

        if pixmap.isNull():
            print("截图失败：获取的图像无效")
            return

        buffer = QBuffer()
        buffer.open(QBuffer.ReadWrite)
        pixmap = pixmap.scaled(1280, 720, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pixmap.save(buffer, "PNG")
        data = buffer.data().toBase64().data().decode()
        image_url = f"data:image/png;base64,{data}"
        self._send_to_vision(
            image_url,
            "请客观、简洁地描述这张屏幕截图的内容，包括可见的窗口、文字、界面元素等。描述将交给主AI作为上下文。"
        )


    def _capture(self):
        print(" -----[ Action ]----- ", "\n",
              "[", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "]", "\n",
              "\"", "雨竹看了一眼你的屏幕", "\"","\n")
        self.capture()
        

    def _on_feed(self):
        dialog = FeedDialog(self._satiety_level, self)
        dialog.food_selected.connect(self._on_food_selected)
        dialog.exec_()

    def _on_food_selected(self, food):
        was_full = self._satiety_level >= FULL_THRESHOLD
        self._feed(food["amount"])
        if was_full and food["type"] == "snack":
            msg = "虽然已经饱了，但零食还是吃得下~"
        else:
            msg = f"谢谢投喂{food['name']}~好好吃！"
        self._content_bar.show_content(msg)
        if self._ai:
            type_desc = "零食" if food["type"] == "snack" else "主食"
            notify = (f"（系统事件：用户刚刚投喂了雨竹。食物：{food['name']}；"
                      f"回复饱食度：{food['amount']}；食品类型：{type_desc}。"
                      f"雨竹当前饱食度：{self._satiety_level}/100。）")
            print(" -----[ Action ]----- ", "\n",
              "[", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "]", "\n",
              "\"", f"你投喂了{food['name']}给雨竹", "\"","\n")
            self._ai.send_message(notify)

    def _on_action(self):
        action_prompt = "用户摸了摸你的头"
        print(" -----[ Action ]----- ", "\n",
              "[", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "]", "\n",
              "\"", "你摸了摸雨竹的头", "\"","\n")
        self._ai.send_message(action_prompt)

    def _on_vision_describe(self, description):
        self._vision_busy = False
        if self._vision_ai is not None:
            self._vision_ai.set_system_prompt("")
        if self._ai is not None:
            user_msg = f"现在是{datetime.now().strftime('%Y-%m-%d %H:%M:%S') }我刚发了一张屏幕截图给你，以下是图片内容描述：\n{description}\n请基于这个描述回复我。"
            self._ai.send_message(user_msg)
        else:
            self._on_ai_response(description)

    def _on_config_saved(self, config):
        self._config = config
        self._apply_size_config()
        self._apply_satiety_config()
        self._apply_poller_config()
        if self._ai:
            self._ai.update(
                config.get("provider", "stepfun"),
                config.get("api_key", ""),
                config.get("tavily_api_key", ""),
            )

        if self._vision_ai is not None:
            self._vision_ai.update(
                config.get("vision_provider", "stepfun"),
                config.get("vision_api_key", "") or config.get("api_key", ""),
                "",
            )

    def _card_rect(self):
        return QRectF(15, 15, self.width() - 30, self.height() - 30)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        card = self._card_rect()

        for i in range(4):
            offset = 9 - i * 2.25
            r = card.adjusted(-offset, -offset + 3, offset, offset + 3)
            alpha = 8 + i * 8
            painter.setBrush(QBrush(QColor(60, 65, 80, alpha)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(r, 18 + offset, 18 + offset)

        painter.setBrush(QBrush(QColor(251, 251, 253)))
        painter.setPen(QPen(QColor(230, 232, 236), 0.5))
        painter.drawRoundedRect(card, 18, 18)

        painter.save()
        clip_path = QPainterPath()
        clip_path.addRoundedRect(card, 18, 18)
        painter.setClipPath(clip_path)
        painter.drawPixmap(card.toRect(), self.image)
        painter.restore()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 18, 18)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def _not_image(self):
        self._content_bar.show_content("不是图片文件，拖进来也没用ww")

    def _no_vlm(self):
        self._content_bar.show_content("没有VLM API哦，请使用StepFun API或等待下版本对其他VLM的支持。")

    def _image(self,data):
        print(" -----[ user input ]----- ", "\n",
              "[", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "]", "\n",
              "\"", "图片", "\"",'\n')
        self._send_to_vision(
            data,
            "请客观、简洁地描述这张图片的内容。描述将交给主AI作为上下文。"
        )