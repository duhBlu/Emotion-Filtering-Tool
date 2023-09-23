import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class GalleryView(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.initialized = True
        self.create_widgets()
        self.current_row = 0
        self.current_col = 0


    def create_widgets(self):
        # Configure canvas and scrollbar
        self.canvas = tk.Canvas(self)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create frame to hold images
        self.frame_images = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame_images, anchor="nw", tags="self.frame_images")

        self.frame_images.bind("<Configure>", self.on_frame_configure)
        self.status_label = ttk.Label(self, text="")
        self.status_label.grid(row=1, column=0, columnspan=2, sticky="w")


    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


# NO WORK
# currently not working. Images are not displaying. I think they may need to be resized. 
# Also the scrollable grid box and maximum images per line should be dynamically changed.
    def add_image_to_gallery(self, images):
        if not isinstance(images, list):
            images = [images]

        # Ensure you have an attribute to store PhotoImage references
        if not hasattr(self, 'photo_images'):
            self.photo_images = []

        # Convert PIL images to PhotoImage and append to the list
        new_photo_images = [ImageTk.PhotoImage(img) for img in images]
        self.photo_images.extend(new_photo_images)

        # Display the new images in the frame
        for i, photo in enumerate(new_photo_images):
            label = ttk.Label(self.frame_images, image=photo)
            label.grid(row=self.current_row, column=self.current_col, sticky="nsew")  # 3 images per row
            self.current_col += 1
            if self.current_col > 2:
                self.current_col = 0
                self.current_row += 1

            # Update status label
            self.status_label.config(text=f"Processed {len(self.photo_images)} images")
            self.update()  # Force the application to update the GUI


        
