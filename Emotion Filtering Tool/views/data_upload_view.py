# Similarly, for gallery view
import tkinter as tk
from tkinter import ttk

class DataUploadView(ttk.Frame):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        label = ttk.Label(self, text="This is the Data Upload View!")
        label.pack(pady=20, padx=20)
