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

        # Dictionary to store views (frames) to show/hide
        self.views = {}
        self.current_view = None
        
        # Create the view frames but don't display them yet
        self.views['Data Upload & Image Selection'] = DataUploadView(self)
        self.views['Gallery'] = GalleryView(self)
        self.views['Manual Image Review'] = ManualReviewView(self)
        self.views['Image Augmentation'] = AugmentationView(self)
        self.views['Dataset Export Options'] = ExportOptionView(self)


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
                btn.config(bg="#e5e5e5", fg="#363636")
            btn.grid(row=idx, column=0, sticky='nsew')
            self.buttons[btn_text] = btn  # Store the button reference
            

        buffer = tk.Frame(self.view_container, bg='white')
        buffer.grid(row=0, column=0, sticky='nsew', padx=1000, pady=1000) 

        for name in self.views:
            view = self.views[name]
            view.grid(in_=self.view_container, row=0, column=0, sticky='nsew')
            view.lower(buffer) 
            
        self.change_view('Data Upload & Image Selection')
                    
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
       
    # cleanup system made folders
    def destroy(self):
        self.views['Data Upload & Image Selection'].cancellation_requested = True
        data_upload_view = self.views.get('Data Upload & Image Selection')
    
        if data_upload_view:
            # Delete the entire extracted_dir
            if os.path.exists(data_upload_view.extract_dir):
                print(f"Deleting {data_upload_view.extract_dir}")
                for root, dirs, _ in os.walk(data_upload_view.extract_dir, topdown=False):
                    for dir in dirs:
                        print(f"removing: {dir}")
                    print(f"removing: {root}")
                shutil.rmtree(data_upload_view.extract_dir)
                
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

