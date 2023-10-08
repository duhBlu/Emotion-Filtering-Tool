import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from io import BytesIO
import os
from tkinter import NW, NE

class GalleryView(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.initialized = True
        self.candidate_images = []
        self.image_tag_mappings = {}
        self.current_row = 0
        self.current_col = 0
        # Configure the main frame's row and column weights
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)  # This ensures scrollbar remains to the right
        self.create_widgets()

    def create_widgets(self):
        # Configure canvas and scrollbar
        self.canvas = tk.Canvas(self)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky='nse')
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Create frame to hold images
        self.frame_images = ttk.Frame(self.canvas)
        self.frame_images.grid_columnconfigure(0, weight=1)  # This allows column 0 in frame_images to expand with the canvas
        self.canvas.create_window((0, 0), window=self.frame_images, anchor="nw")

        self.frame_images.bind("<Configure>", self.on_frame_configure)
        self.frame_images.bind("<MouseWheel>", self._on_mousewheel)

        self.status_label = ttk.Label(self, text="")
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="w")

        # Configure rows and columns to adjust dynamically
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        
        # Review button
        self.review_button = ttk.Button(self, text="Send to Manual Review", command=self.send_to_review)
        self.review_button.grid(row=1, column=0, padx=20, pady=20, sticky='e')

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta//120), "units")
        
    def send_to_review(self):
        self.master.views['Manual Image Review'].show_images(self.candidate_images)
        self.master.change_view('Manual Image Review')

    def receive_data(self, candidate_folder, image_tag_mapping):
        self.candidate_folder = candidate_folder
        self.image_tag_mapping = image_tag_mapping
        # Assuming the image path is the key in the image_tag_mapping dictionary
        print(list(image_tag_mapping.keys())[0])
        image_path = list(image_tag_mapping.keys())[0] if image_tag_mapping else None
        if image_path:
            self.load_single_image(image_path)
        
    def load_single_image(self, image_path):
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            image = Image.open(BytesIO(image_data))
            resized_image = self.resize_image(image)
            tags = self.image_tag_mapping.get(image_path, [])  # Fetch tags for this image if any
            self.add_image_to_gallery(resized_image, tags)
            print(f"Loaded {image_path}")
        except Exception as e:
            print(f"Error loading image {os.path.basename(image_path)}: {e}")

    
    def resize_image(self, image, max_width=300, max_height=300):
        # Resize image while maintaining its aspect ratio
        original_width, original_height = image.size
        aspect_ratio = original_width / original_height
        if original_width > max_width or original_height > max_height:
            if original_width > original_height:
                new_width = max_width
                new_height = int(new_width / aspect_ratio)
            else:
                new_height = max_height
                new_width = int(new_height * aspect_ratio)
            image = image.resize((new_width, new_height))
        return image

    def add_image_to_gallery(self, image, tags):
        try:
            photo = ImageTk.PhotoImage(image)
            self.candidate_images.append(photo)  # Store a reference to the PhotoImage object
            
            img_label = ttk.Label(self.frame_images, image=photo)
            img_label.grid(row=self.current_row, column=self.current_col, sticky="nw", padx=5, pady=5)  
            img_label.bind("<MouseWheel>", self._on_mousewheel)
            print(tags)
            # Add tags as a label to the image
            if tags:
                tag_text = ", ".join(tags)
                tag_label = ttk.Label(self.frame_images, text=tag_text, background='white', anchor='e')
                tag_label.grid(row=self.current_row, column=self.current_col, sticky="ne", padx=5, pady=5)

        except Exception as e:
            print(f"Error displaying image: {e}")

        self.current_col += 1
        if self.current_col > 3:
            self.current_col = 0
            self.current_row += 1

        # Update scrollregion after adding the image
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        self.update()  # Force the application to update the GUI
        self.canvas.update_idletasks()






        
