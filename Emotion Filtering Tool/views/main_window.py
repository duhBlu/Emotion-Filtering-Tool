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

        # Configure the main frame's rows and columns
        for i in range(5):
            self.grid_rowconfigure(i, weight=1)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=6)

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

        # Create ttk Style for customizing buttons
        self.style = ttk.Style()
        self.style.configure(
            "Custom.TButton",
            font=("Arial", 12), 
            foreground="blue"
        )

        # Create buttons on the left side with the custom style
        buttons = ['Data Upload & Image Selection', 
                   'Gallery', 
                   'Manual Image Review', 
                   'Image Augmentation', 
                   'Dataset Export Options']

        for idx, btn_text in enumerate(buttons):
            btn = ttk.Button(
                self, 
                text=btn_text, 
                command=lambda v=btn_text: self.change_view(v), 
                style="Custom.TButton"  # Apply the custom style
            )
            btn.grid(row=idx, column=0, sticky='nsew')

        self.change_view('Data Upload & Image Selection')
        
        # try:
        #     subprocess.run(['dvc', 'init', '--no-scm'], check=True, capture_output=True)
        # except subprocess.CalledProcessError as e:
        #     print(f'Failed to initialize DVC: {e.stderr.decode()}')


    def change_view(self, view_name):
        if self.current_view:
            self.current_view.grid_forget()  # This hides the currently visible view

        new_view = self.views.get(view_name)
        if new_view:
            # Using the container frame to grid the new_view
            new_view.grid(in_=self.view_container, row=0, column=0, sticky='nsew')
            self.current_view = new_view

    def destroy(self):
        # Add code to delete the extracted folders
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
    # Allow the main frame to grow and shrink with the window
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    # Create the main window frame
    main_win = MainWindow(master=root)
    main_win.grid(row=0, column=0, sticky='nsew')
    
    root.protocol("WM_DELETE_WINDOW", main_win.destroy)

    root.mainloop()

