# The entry point of the application, where everything gets wired up and started

import sys
from PyQt5.QtWidgets import QApplication
from controllers.main_controller import MainController

if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = MainController()
    sys.exit(app.exec_())
