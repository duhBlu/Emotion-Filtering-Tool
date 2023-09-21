# The entry point of the application, where everything gets wired up and started


import sys
import tkinter as tk
from views.main_window import MainWindow
from ttkthemes import ThemedTk

if __name__ == "__main__":
    root = ThemedTk(theme="arc")
    root.title('EFT Image Application')
    root.geometry('800x600')

    main_win = MainWindow(master=root)
    root.mainloop()
