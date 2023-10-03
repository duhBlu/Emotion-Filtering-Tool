# The main UI window that houses all other views

import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from views.data_upload_view import DataUploadView
from views.gallery_view import GalleryView
from views.manual_review import ManualReviewView
from views.augmentation_view import AugmentationView
from views.export_options_view import ExportOptionView


class MainWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.grid(sticky='nsew')

        # Configure the main frame's rows and columns
        for i in range(5):  # Assuming you have 5 buttons
            self.grid_rowconfigure(i, weight=1)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=5)

        # Create a container frame to hold the views
        self.view_container = tk.Frame(self)
        self.view_container.grid(row=0, column=1, rowspan=5, sticky='nsew')
        self.view_container.grid_rowconfigure(0, weight=1)
        self.view_container.grid_columnconfigure(0, weight=1)

        # Dictionary to store views (frames) to show/hide
        self.views = {}
        self.current_view = None

        # Create the view frames but don't display them yet
        self.views['Gallery'] = GalleryView(self)
        self.views['Data Upload & Image Selection'] = DataUploadView(self, gallery_view=self.views['Gallery'])
        self.views['Manual Image Review'] = ManualReviewView(self)
        self.views['Image Augmentation'] = AugmentationView(self)
        self.views['Dataset Export Options'] = ExportOptionView(self)

        # Create buttons on the left side
        buttons = ['Data Upload & Image Selection', 
                   'Gallery', 
                   'Manual Image Review', 
                   'Image Augmentation', 
                   'Dataset Export Options']

        for idx, btn_text in enumerate(buttons):
            btn = ttk.Button(self, text=btn_text, command=lambda v=btn_text: self.change_view(v))
            btn.grid(row=idx, column=0, sticky='nsew')

        self.change_view('Data Upload & Image Selection')

    def change_view(self, view_name):
        if self.current_view:
            self.current_view.grid_forget()  # This hides the currently visible view

        new_view = self.views.get(view_name)
        if new_view:
            if hasattr(new_view, 'show'):
                new_view.show()
            # Using the container frame to grid the new_view
            new_view.grid(in_=self.view_container, row=0, column=0, sticky='nsew')
            self.current_view = new_view

