from msilib.schema import TextStyle
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from io import BytesIO
import os

class GalleryView(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.initialized = True
        self.candidate_images = []
        self.image_tag_mappings = {}
        self.image_positions = []
        self.row_heights = []
        self.current_col = 0
        self.current_row = 0
        self.current_col = 0
        self.current_row = 0
        self.current_row_width = 0 
        # Configure the main frame's row and column weights
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)  # This ensures scrollbar remains to the right
        self.create_widgets()

    def create_widgets(self):
        # Configure canvas and scrollbar
        self.canvas = tk.Canvas(self)
        self.canvas.grid(row=1, column=0, sticky="nsew")
        
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, rowspan=3, sticky='nse')
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Create frame to hold images
        self.frame_images = ttk.Frame(self.canvas)
        self.frame_images.grid_columnconfigure(0, weight=1)  # This allows column 0 in frame_images to expand with the canvas
        self.canvas.create_window((0, 0), window=self.frame_images, anchor="nw")

        self.frame_images.bind("<Configure>", self.on_frame_configure)
        self.frame_images.bind("<MouseWheel>", self._on_mousewheel)

        # Review button
        self.review_button = ttk.Button(self, text="Send to Manual Review", command=self.send_to_review)
        self.review_button.grid(row=2, column=0, padx=20, pady=20, sticky='e')
        
        # progress bar
        self.progress_var = tk.IntVar() 
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.grid(row=0, column=0, columnspan=2, pady=20, padx=(30, 20), sticky='ew')
        label_font = ("Helvetica", 14)
        # Label to display the progress
        self.progress_label = ttk.Label(self, text="0/0", font=label_font)
        self.progress_label.grid(row=0, column=0, pady=20, padx=(10, 15), sticky='w')

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta//120), "units")
     
    def set_progress_maximum(self, max_value):
            self.progress_bar["maximum"] = max_value

    def update_progress(self, value):
        # if(value > self.progress_bar["maximum"]):
        #     value = self.progress_bar["maximum"]
        self.progress_var.set(value)
        self.progress_label["text"] = f"{value}/{self.progress_bar['maximum']}"
        
    # DEV NOTE
    # change this to not send images that have previously been sent to manual review
    # to avoid duplicates 
    def send_to_review(self):
        self.master.views['Manual Image Review'].show_images(self.candidate_images)
        self.master.change_view('Manual Image Review')

    # recieves the images from the candidate folder, along with their tags
    def receive_data(self, candidate_folder, image_tag_mapping):
        self.candidate_folder = candidate_folder
        # Combine with existing image_tag_mappings if present
        self.image_tag_mappings = {**self.image_tag_mappings, **image_tag_mapping}
        image_path = list(image_tag_mapping.keys())[0] if image_tag_mapping else None
        features = image_tag_mapping.get(image_path, {}).get('tags', None)
        if features:
            self.load_single_image(image_path, features)

    def load_single_image(self, image_path, features=None):
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            image = Image.open(BytesIO(image_data))
        
            # Assuming you have a way to get the display width, replace 'display_width' with actual width value
            resized_image = self.resize_image_to_display_width(image, 200)  
        
            tags = features if features is not None else self.image_tag_mapping.get(image_path, [])  # Fetch tags for this image if any
            self.add_image_to_gallery(resized_image, tags)
            print(f"Loaded {image_path} with tags: {tags}")
        except Exception as e:
            print(f"Error loading image {os.path.basename(image_path)}: {e}")

    def resize_image_to_display_width(self, image, display_width):
        # Resize image to fit the display width while maintaining its aspect ratio
        original_width, original_height = image.size
        aspect_ratio = original_width / original_height
        new_width = display_width
        new_height = int(new_width / aspect_ratio)
        image = image.resize((new_width, new_height))
        return image

    def add_image_to_gallery(self, image, tags):
        try:
            photo = ImageTk.PhotoImage(image)
            self.candidate_images.append(photo)  # Store a reference to the PhotoImage object
            
            # Calculate image's contribution to row width (including padding)
            image_width_with_padding = photo.width() + 10  # Assuming 5-pixel padding on each side
            
            # Check if adding this image would exceed the max frame width
            if self.current_row_width + image_width_with_padding > self.canvas.winfo_width():
                # Reset for new row
                self.current_row_width = 0
                self.current_col = 0
                self.current_row += 1
            
            img_label = ttk.Label(self.frame_images, image=photo)
            img_label.grid(row=self.current_row, column=self.current_col, sticky="nw", padx=5, pady=5)  
            img_label.bind("<MouseWheel>", self._on_mousewheel)
            print(tags)
            
            # Add tags as a label to the image
            if tags:
                tag_text = ", ".join(tags)
                tag_label = ttk.Label(self.frame_images, text=tag_text, background='white', anchor='e')
                tag_label.grid(row=self.current_row, column=self.current_col, sticky="ne", padx=5, pady=5)

            # Update current row width and column
            # Update current row width and column
            self.current_row_width += image_width_with_padding
            self.current_col += 1
        
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

            self.update()  # Force the application to update the GUI
            self.canvas.update_idletasks()

        except Exception as e:
            print(f"Error displaying image: {e}")




        
