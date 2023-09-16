# The main UI window that houses all other views

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the main window
        self.initUI()
        # Window settings
        self.setWindowTitle('EFT Image Application')
        self.setGeometry(100, 100, 800, 600)

        # Create the main container
        self.container = QVBoxLayout()

        # Create the tab widget
        self.tabs = QTabWidget()
        self.container.addWidget(self.tabs)

        # Create tabs
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()
        self.tab5 = QWidget()

        # Add tabs to the widget
        self.tabs.addTab(self.tab1, "Gallery View")
        self.tabs.addTab(self.tab2, "Data Upload & Image Selection")
        self.tabs.addTab(self.tab3, "Detailed Image Review")
        self.tabs.addTab(self.tab4, "Augmentation View")
        self.tabs.addTab(self.tab5, "Dataset Export Options")

        # Create a main widget for the main window and set the layout
        self.main_widget = QWidget(self)
        self.main_widget.setLayout(self.container)
        self.setCentralWidget(self.main_widget)

        # Show the main window
        self.show()

    def initUI(self):
        # Initialize UI components
        pass
