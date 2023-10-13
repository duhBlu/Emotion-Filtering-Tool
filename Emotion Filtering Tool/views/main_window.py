import tkinter as tk
from tkinter import ttk
import shutil
import os
import subprocess
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

        # make 5 rows for the 5 buttons
        for i in range(5):
            self.grid_rowconfigure(i, weight=1)

        self.grid_columnconfigure(0, weight=0) # button, weight 0 so no grow
        self.grid_columnconfigure(1, weight=6) # main content section, weight so it grow

        # Create a container frame to hold the views
        self.view_container = tk.Frame(self)
        self.view_container.grid(row=0, column=1, rowspan=5, sticky='nsew')
        self.view_container.grid_rowconfigure(0, weight=1)
        self.view_container.grid_columnconfigure(0, weight=1)

        # Dictionary to store views (frames) to show/hide
        self.views = {}
        self.current_view = None
        
        # Create the view frames but don't display them yet
        self.views['Data Upload & Image Selection'] = DataUploadView(self)
        self.views['Gallery'] = GalleryView(self)
        self.views['Manual Image Review'] = ManualReviewView(self)
        self.views['Image Augmentation'] = AugmentationView(self)
        self.views['Dataset Export Options'] = ExportOptionView(self)

        # Unselected button color
        self.style = ttk.Style()
        self.style.configure(
            "Custom.TButton",
            font=("Arial", 12), 
            foreground="blue",
            background="SystemButtonFace"
        )
        # Selected button color
        self.style.configure(
            "Selected.TButton",
            font=("Arial", 12),
            foreground="white",
            background="blue"
        )

        # Make the list of buttons
        buttons = ['Data Upload & Image Selection', 
                   'Gallery', 
                   'Manual Image Review', 
                   'Image Augmentation', 
                   'Dataset Export Options']
        
        self.buttons = {}  # dictionary to store references to the button
        for idx, btn_text in enumerate(buttons):
            btn = tk.Button(
                self, 
                text=btn_text, 
                command=lambda v=btn_text: self.change_view(v), 
                takefocus=0  
            )
            if(btn_text == 'Data Upload & Image Selection'):
                btn.config(bg="#e5e5e5", fg="#0c0c0c")
            btn.grid(row=idx, column=0, sticky='nsew')
            self.buttons[btn_text] = btn  # Store the button reference
            
        self.change_view('Data Upload & Image Selection')

        buffer = tk.Frame(self.view_container, bg='white')
        buffer.grid(row=0, column=0, sticky='nsew', padx=1000, pady=1000) 

        for name in self.views:
            view = self.views[name]
            view.grid(in_=self.view_container, row=0, column=0, sticky='nsew')
            view.lower(buffer)

    def change_view(self, view_name):
        if view_name in self.views:
            for name, view in self.views.items():
                if name == view_name:
                    view.lift()
            for name, btn in self.buttons.items():
                if name == view_name:
                    btn.config(bg="#e5e5e5", fg="#0c0c0c") 
                else:
                    btn.config(bg="#bfbfbf", fg="#0c0c0c")
       
    # cleanup system made folders
    def destroy(self):
        data_upload_view = self.views.get('Data Upload & Image Selection')
        if data_upload_view:
            for root_folder, subfolders in data_upload_view.extracted_folders_dict.items():
                if os.path.exists(root_folder):
                    shutil.rmtree(root_folder)
                    print(f"Deleted root folder: {root_folder}")
            
            # Clear the dictionary
            data_upload_view.extracted_folders_dict.clear()
        root.quit()        
    

if __name__ == "__main__":
    root = ThemedTk(theme="breeze")
    root.title('Emotion Filtering Tool')
    root.wm_state('zoomed')
    
    # create main root grid. 1x1 so main window grows with the size of the screen
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # create the root window
    main_win = MainWindow(master=root)
    main_win.grid(row=0, column=0, sticky='nsew')
    
    root.protocol("WM_DELETE_WINDOW", main_win.destroy)

    root.mainloop()

