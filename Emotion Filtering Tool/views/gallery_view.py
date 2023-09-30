import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import asyncio
import aiofiles
from io import BytesIO
import os

class GalleryView(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.initialized = True
        self.photo_images = []
        self.current_row = 0
        self.current_col = 0
        self.c = 0
        # Configure the main frame's row and column weights
        self.grid_rowconfigure(0, weight=1)
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
        self.frame_images.bind("<Button-4>", self._on_mousewheel_up)
        self.frame_images.bind("<Button-5>", self._on_mousewheel_down)

        self.status_label = ttk.Label(self, text="")
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="w")

        # Configure rows and columns to adjust dynamically
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta//120), "units")

    def _on_mousewheel_up(self, event):
        self.canvas.yview_scroll(-1, "units")

    def _on_mousewheel_down(self, event):
        self.canvas.yview_scroll(1, "units")
        
    def load_images_from_folder(self, folder_paths):
        for folder_path in folder_paths:
            for img_file in os.listdir(folder_path):
                img_path = os.path.join(folder_path, img_file)
                if os.path.isfile(img_path) and img_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                    try:
                        with open(img_path, 'rb') as f:
                            image_data = f.read()
                        image = Image.open(BytesIO(image_data))
                        self.resize_image(image)
                        self.add_image_to_gallery(image)
                        print(f"Loaded {img_path}")
                    except Exception as e:
                        print(f"Error loading image {os.path.basename(img_path)}: {e}")
                    # limits how many image will be shown for now TEMPORARY
                    self.c += 1
                    if(self.c == 500):
                        break
    
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

    def add_image_to_gallery(self, image):
        try:
            photo = ImageTk.PhotoImage(self.resize_image(image))
            self.photo_images.append(photo)
            img_label = ttk.Label(self.frame_images, image=photo)
            img_label.grid(row=self.current_row, column=self.current_col, sticky="nw", padx=5, pady=5)  
            img_label.bind("<MouseWheel>", self._on_mousewheel)
            img_label.bind("<Button-4>", self._on_mousewheel_up)
            img_label.bind("<Button-5>", self._on_mousewheel_down)
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





        
