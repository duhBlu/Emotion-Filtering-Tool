import tkinter as tk
from tkinter import ttk

class ExportOptionView(ttk.Frame):
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)
        label = ttk.Label(self, text="This is the Export Options View!")
        label.pack(pady=20, padx=20)
