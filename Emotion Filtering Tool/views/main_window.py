# The main UI window that houses all other views

# The main UI window that houses all other views

import tkinter as tk
from tkinter import ttk


class MainWindow(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        # Window settings
        self.master.title('EFT Image Application')
        self.master.geometry('800x600')
        
        # Create tabs
        self.tabs = ttk.Notebook(self.master)
        self.tab1 = ttk.Frame(self.tabs)
        self.tab2 = ttk.Frame(self.tabs)
        self.tab3 = ttk.Frame(self.tabs)
        self.tab4 = ttk.Frame(self.tabs)
        self.tab5 = ttk.Frame(self.tabs)

        # Add tabs to the widget
        self.tabs.add(self.tab1, text="Gallery View")
        self.tabs.add(self.tab2, text="Data Upload & Image Selection")
        self.tabs.add(self.tab3, text="Detailed Image Review")
        self.tabs.add(self.tab4, text="Augmentation View")
        self.tabs.add(self.tab5, text="Dataset Export Options")

        self.tabs.pack(expand=1, fill='both')

        # Initialize UI components
        self.initUI()

    def initUI(self):
        # Initialize UI components for tabs here if needed
        # For example:
        # label1 = tk.Label(self.tab1, text="This is Gallery View")
        # label1.pack(pady=20, padx=20)
        pass
