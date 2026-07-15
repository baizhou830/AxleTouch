import sys
from AIclient import Client_creater
from PyQt5.QtWidgets import QApplication
from widgets import EdgeFloatingBlock
from config_manager import load_config


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EdgeFloatingBlock()
    config = load_config()
    ai = Client_creater(config)
    ai.set_system_prompt(config.get("prompt", ""))
    window.set_ai_client(ai, config)
    window.show()
    sys.exit(app.exec_())

