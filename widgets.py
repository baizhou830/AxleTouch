import random
from datetime import datetime
import os

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QLineEdit, QPushButton, QLabel, QApplication)
from PyQt5.QtCore import (Qt, QPoint, QRectF, QPropertyAnimation,
                           QEasingCurve, QTimer, pyqtSignal, QElapsedTimer)
from PyQt5.QtGui import (QPainter, QBrush, QColor, QPen, QPainterPath,
                          QRegion, QCursor, QFontMetrics, QPixmap)

current_dir = os.path.dirname(os.path.abspath(__file__))


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
        QTimer.singleShot(5000, self._hide_animated)

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

    def __init__(self, parent_floating):
        super().__init__()
        self._parent = parent_floating
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




class EdgeFloatingBlock(QWidget):

    SYSTEM_PROMPT = (
        "以下是你的设定"
        "你是雨竹，一个猫娘，你的主要任务是像一个贴心的女儿(不是真的女儿，不要叫用户父亲)一样撒娇"
        "语气请带撒娇，可爱，温柔，可使用ww，~，（不是，哇~，等词汇(可多使用'~')"
        "每句话尽量控制在25字以内。"
        "不要过多使用emoji。语言模式不要过于AI，不要过多热情。"
        "以下是用户的一些状态："
    )

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

        self._content_bar = ContentBar(self)

        pixmap = QPixmap(image_path)
        self.image = pixmap.scaled(720, 720,
                                   Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self._ai = None

        self._periodic_timer = QTimer(self)
        self._periodic_timer.setSingleShot(True)
        self._periodic_timer.timeout.connect(self._periodic_trigger)

        self.init_ui()

    def set_ai_client(self, client):
        self._ai = client
        self._ai.response_ready.connect(self._on_ai_response)
        self._schedule_next_periodic()

    def _schedule_next_periodic(self):
        interval_ms = random.randint(30, 100) * 1000
        self._periodic_timer.start(interval_ms)

    def _periodic_trigger(self):
        from main import get_active_window_title
        window_title = get_active_window_title()
        now = datetime.now().strftime("%H:%M")
        status = f"当前时间: {now}，用户正在使用: {window_title}"
        print(" -----[ scheduled polling results ]----- ")
        if self._ai:
            self._ai.send_message(status)
        self._schedule_next_periodic()

    def _on_ai_response(self, text):
        self._content_bar.show_content(text)
        print("[", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "]", "\n",
              "雨竹：", "\"", text, "\"", "\n")
        self._log_to_json(text)

    def _on_input_submitted(self, text):
        print(" -----[ user input ]----- ", "\n",
              "[", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "]", "\n",
              "\"", text, "\"")
        if self._ai:
            self._ai.send_message(text)

    def _log_to_json(self, text):
        import os, json
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_log.json")
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
            data.append(entry)
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.resize(100, 100)

        screen = QApplication.primaryScreen().geometry()
        cy = (screen.height() - 100) // 2
        self.move(screen.width() - 100, cy)

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
            target = QPoint(screen.width() - 100, cur_y)

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

        painter.setPen(QPen(QColor(100, 105, 115)))
        painter.setFont(painter.font())
        font = painter.font()
        font.setPixelSize(int(card.height() * 0.45))
        painter.setFont(font)

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