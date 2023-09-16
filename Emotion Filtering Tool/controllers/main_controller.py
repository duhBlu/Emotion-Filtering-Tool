# General control logic, instantiating other controllers

from models.image_model import ImageModel
from views.main_window import MainWindow

class MainController:
    def __init__(self):
        self.model = ImageModel()
        self.view = MainWindow()

        # Connect signals and slots, for example:
        # self.view.someButton.clicked.connect(self.some_method)

    def some_method(self):
        # Handle some logic
        pass
