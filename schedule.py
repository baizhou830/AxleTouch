# schedule.py
import random
from datetime import datetime
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

class Poller(QObject):

    status_ready = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._trigger)
        self._schedule_next()

    def _schedule_next(self):
        interval_ms = random.randint(30, 100) * 1000
        self._timer.start(interval_ms)

    def _trigger(self):
        from tools import get_active_window_title
        window_title = get_active_window_title()
        now = datetime.now().strftime("%H:%M")
        status = f"当前时间: {now}，用户正在使用: {window_title}"
        print(" -----[ scheduled polling results ]----- ")
        self.status_ready.emit(status)
        self._schedule_next()