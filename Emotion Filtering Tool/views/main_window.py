import tkinter as tk
import shutil
import os
from turtle import backward
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

        self.master_image_dict = {} # dictionary to store all images and associated data
        
        # Dictionary to store views (frames) to show/hide
        self.views = {}
        self.current_view = None
        
        # Create the view frames but don't display them yet
        self.views['Upload'] = DataUploadView(self)
        self.views['Gallery'] = GalleryView(self)
        self.views['Manual'] = ManualReviewView(self)
        self.views['Augment'] = AugmentationView(self)
        self.views['Export'] = ExportOptionView(self)


        # Make the list of buttons
        buttons = ['Upload', 'Gallery', 'Manual', 'Augment', 'Export']
        self.buttons = {}  # dictionary to store references to the button
        for idx, btn_text in enumerate(buttons):
            btn = tk.Button(
                self,
                text=btn_text, 
                borderwidth=1,
                width=20,
                command=lambda v=btn_text: self.change_view(v), 
                takefocus=0  
            )
            if(btn_text == 'Upload'):
                btn.config(bg="#e5e5e5", fg="#363636")
            btn.grid(row=idx, column=0, sticky='nsew')
            btn.bind("<Enter>", self.on_enter)
            btn.bind("<Leave>", self.on_leave)
            self.buttons[btn_text] = btn  # Store the button reference
            

        buffer = tk.Frame(self.view_container, bg='white')
        buffer.grid(row=0, column=0, sticky='nsew', padx=1000, pady=1000) 

        for name in self.views:
            view = self.views[name]
            view.grid(in_=self.view_container, row=0, column=0, sticky='nsew')
            view.lower(buffer) 
            
        self.change_view('Upload')
        
    def on_enter(self, event):
        event.widget.config(bg='#c85961')

    def on_leave(self, event):
        event.widget.config(bg='#bfbfbf')

            
    def change_view(self, view_name):
        if view_name in self.views:
            for name, view in self.views.items():
                if name == view_name:
                    view.lift()
            for name, btn in self.buttons.items():
                if name == view_name:
                    btn.config(bg="#e5e5e5", fg="#363636") 
                else:
                    btn.config(bg="#bfbfbf", fg="#262626")
                    
    def add_image_to_master_dict(self, file_path, tags, photo_object, current_directory):
        # Add an entry to the master image dictionary
        self.master_image_dict[file_path] = {
            "working_directory": current_directory,
            "photo_object": photo_object,
            "tags": tags
        }    

    def setup_directories(self):
        # Define the root working directory within the user's home directory
        home_dir = os.path.expanduser('~')
        self.working_directory = os.path.join(home_dir, "Emotion Filtering Tool", "working_directory")

        # Define subdirectories
        self.subdirectories = {
            'extracted_images': os.path.join(self.working_directory, "extracted_images"),
            'pending_review': os.path.join(self.working_directory, "pending_review"),
            'candidates': os.path.join(self.working_directory, "candidates"),
            'accepted_images': os.path.join(self.working_directory, "accepted_images"),
        }
        self.extracted_images_dir = self.subdirectories['extracted_images']
        self.pending_review_dir = self.subdirectories['pending_review']
        self.candidates_dir = self.subdirectories['candidates']
        self.accepted_images_dir = self.subdirectories['accepted_images']

        # Create the subdirectories if they don't exist, clear them if they do
        for key, dir_path in self.subdirectories.items():
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            else:
                if key == 'extracted_images':
                    # For 'extracted_images', remove subdirectories too
                    for root, dirs, files in os.walk(dir_path):
                        for dir in dirs:
                            shutil.rmtree(os.path.join(root, dir))
                # For all directories, clear files
                for filename in os.listdir(dir_path):
                    file_path = os.path.join(dir_path, filename)
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):  # if there are directories in other than 'extracted_images'
                        shutil.rmtree(file_path)
                        
    def destroy(self):
        # Call the superclass destroy method
        super().destroy()
    
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
    main_win.setup_directories() 
    root.protocol("WM_DELETE_WINDOW", main_win.destroy)

    root.mainloop()

