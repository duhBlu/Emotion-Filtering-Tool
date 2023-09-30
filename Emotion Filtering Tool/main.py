# The entry point of the application, where everything gets wired up and started


import sys
import tkinter as tk
from views.main_window import MainWindow
from ttkthemes import ThemedTk


if __name__ == "__main__":
    root = ThemedTk(theme="arc")
    root.title('Emotion Filtering Tool')

    # Allow the main frame to grow and shrink with the window
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # Create the main window frame
    main_win = MainWindow(master=root)
    main_win.grid(row=0, column=0, sticky='nsew')
    
    root.mainloop()
