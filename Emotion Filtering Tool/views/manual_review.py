import tkinter as tk
from tkinter import ttk
from collections import defaultdict
from PIL import Image, ImageTk
from io import BytesIO

class ManualReviewView(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.photo_images = {}
        self.accepted_images = {}
        self.accepted_count = 0  # count of accepted images
        self.total_accepted_count = 0  # count of accepted images this session
        self.selected_images = defaultdict(bool)
        self.image_frames = {}
        self.current_row = 0 
        self.current_col = 0
        self.current_row_width = 0 
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0) 
        self.create_widgets()

        
    '''
    Initialize UI
    '''
    def create_widgets(self):
        self.canvas = tk.Canvas(self)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky='nse')

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.frame_images = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame_images, anchor="nw")

        self.frame_images.bind("<Configure>", self.on_frame_configure)
        self.frame_images.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.accept_button = ttk.Button(self, text="Accept Selected", command=self.accept_images)
        self.accept_button.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.accepted_count_label = ttk.Label(self, text=f"Accepted Images: {self.accepted_count}")
        self.accepted_count_label.grid(row=1, column=0, padx=10, pady=(10, 0), sticky="n")
        
        self.total_accepted_count_label = ttk.Label(self, text=f"Accepted Images This Session: {self.total_accepted_count}")
        self.total_accepted_count_label.grid(row=1, column=0, padx=10, pady=(10,0), sticky="s")

        self.reject_button = ttk.Button(self, text="Reject Selected", command=self.reject_images)
        self.reject_button.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        
        self.send_to_augment_button = ttk.Button(self, text="Send Accepted to Augmentation", command=self.send_to_augment)
        self.send_to_augment_button.grid(row=2, column=0, padx=10, pady=10, sticky="")
        
    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta//120), "units")
        
    '''
    Send data to Augmentation view
    '''
    def send_to_augment(self):
        self.master.views['Image Augmentation'].show_images(self.accepted_images)
        self.master.change_view('Image Augmentation')
        self.accepted_images = {}
        self.accepted_count = 0
        self.total_accepted_count = 0
        self.accepted_count_label.config(text=f"Accepted Images: {self.accepted_count}")
        self.total_accepted_count_label.config(text=f"Accepted Images this Session: {self.total_accepted_count}")
    
    '''
    Clear Images
    '''
    def clear_review(self):
        """Clears all images from the review view."""
        for widget in self.frame_images.winfo_children():
            widget.destroy()

        # Reset attributes
        self.photo_images = {}
        self.accepted_images = {}
        self.selected_images = defaultdict(bool)
        self.image_frames = {}
        self.current_row = 0 
        self.current_col = 0
        self.current_row_width = 0 
    
    '''
    Load and Display Images
    '''
    def load_candidate_images(self, candidate_images):
        self.photo_images.update(candidate_images)
        self.show_images(self.photo_images, False)
    
    def clear_image_grid(self):
        for widget in self.frame_images.winfo_children():
            widget.destroy()

    def show_images(self, images, clear): 
        if clear:
            self.current_col = 0
            self.current_row = 0
            self.current_row_width = 0
            self.clear_image_grid()
        for idx, (image_path, image_data) in enumerate(images.items()):
            photo = image_data['photo']
            tags = image_data['tags']
            self.add_image_to_review(idx, image_path, photo, tags)

        # Update canvas scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        
    def add_image_to_review(self, idx, image_path, photo, tags):
        image_width_with_padding = photo.width() + 10

        # Check if adding this image would exceed the max frame width
        if self.current_row_width + image_width_with_padding > self.canvas.winfo_width():
            # Reset for new row
            self.current_row_width = 0
            self.current_col = 0
            self.current_row += 1
        
        check_var = tk.IntVar()
        # Image Label
        img_label = ttk.Label(self.frame_images, image=photo)
        img_label.grid(row=self.current_row, column=self.current_col, sticky="nw", padx=5, pady=5)
        img_label.bind("<Button-1>", lambda event, idx=idx, var=check_var: self.image_click(idx, var))
        img_label.bind("<MouseWheel>", self._on_mousewheel)

        # Checkbutton (added to the top-left of the image)
        checkbutton = ttk.Checkbutton(self.frame_images, variable=check_var)
        checkbutton.grid(row=self.current_row, column=self.current_col, sticky="nw", padx=5, pady=5)
        checkbutton['command'] = lambda idx=idx, var=check_var: self.toggle_selection(idx, var)

        # Add tags as a label to the image
        tag_string = ', '.join([f"{v}" for _, v in tags.items()])
        tag_label = ttk.Label(self.frame_images, text=tag_string)
        tag_label.grid(row=self.current_row, column=self.current_col, sticky="ne", padx=5, pady=5)

        # Update current row width and column
        self.current_row_width += image_width_with_padding
        self.current_col += 1

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    '''
    Image Selection/Acceptance/Rejection logic
    '''
    def image_click(self, idx, var):
        # Toggle checkbox state
        var.set(1 - var.get())
        # Update the selection
        self.toggle_selection(idx, var)

    def toggle_selection(self, idx, var):
        self.selected_images[idx] = bool(var.get())

    def accept_images(self):
        self.process_selected_images(accept=True)

    def reject_images(self):
        self.process_selected_images(accept=False)

    def process_selected_images(self, accept=True):
        new_photo_images = {}
        for idx, image_data in enumerate(self.photo_images.items()):
            image_path, tag_data = image_data

            selected = self.selected_images.get(idx)
            
            if accept and selected:
                self.accepted_images[image_path] = tag_data
                self.accepted_count += 1
                self.total_accepted_count += 1  # Incrementing the total accepted count
            elif not selected:
                new_photo_images[image_path] = tag_data
        
        self.photo_images = new_photo_images  # Set photo_images to only the ones not selected
        self.show_images(self.photo_images, True)  # Refresh the view with remaining images
        self.accepted_count_label.config(text=f"Accepted Images: {self.accepted_count}")
        self.total_accepted_count_label.config(text=f"Accepted Images this Session: {self.total_accepted_count}")
        self.selected_images.clear()


    
        
