import os
from random import setstate
import shutil
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from io import BytesIO

class GalleryView(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.image_positions = []
        self.row_heights = []
        self.imageTk_objects = []
        self.candidate_paths = []
        self.sent_paths = []
        self.current_col = 0 # for keeping track of the image positions
        self.current_row = 0
        self.current_row_width = 0 
        self.last_loaded_index = 0
        self.images_loaded = 0
        # Configure the main frame's row and column weights
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.create_widgets()

    '''
    Initialize UI
    ''' 
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
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        

        # Review button
        self.review_button = ttk.Button(self, text="Send to Manual Review", command=self.send_to_review)
        self.review_button.grid(row=2, column=0, padx=20, pady=20, sticky='e')
        
        self.clear_button = ttk.Button(self, text="clear", command=self.clear_gallery)
        self.clear_button.grid(row=2, column=0, padx=(5, 20), pady=20, sticky='w')         

        self.load_more_button = ttk.Button(self, text="Load more", command=self.load_more_images, state=tk.DISABLED)
        self.load_more_button.grid(row=2, column=0, padx=(105, 5), pady=20, sticky='w') 
        
        self.stop_processing_button = ttk.Button(self, text="Stop processing", command=self.stop_processing)
        self.stop_processing_button.grid(row=2, column=0, padx=(205, 5), pady=20, sticky='w') 
        
        self.pause_processing_button = ttk.Button(self, text="Pause Processing", command=self.pause_processing)
        self.pause_processing_button.grid(row=2, column=0, padx=(330, 5), pady=20, sticky='w') 
        
        # progress bar
        self.progress_var = tk.IntVar() 
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.grid(row=0, column=0, columnspan=2, pady=20, padx=(80, 20), sticky='ew')
        label_font = ("Helvetica", 14)
        
        # Label to display the progress
        self.progress_label = ttk.Label(self, text="0/0", font=label_font)
        self.progress_label.grid(row=0, column=0, pady=20, padx=(10, 15), sticky='w')

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta//120), "units")

    '''
    Config UI
    '''  
    def set_progress_maximum(self, max_value):
            self.stop_processing_button["state"] = tk.NORMAL    
            self.progress_bar["maximum"] = max_value

    def update_progress(self, value):
        self.progress_var.set(value)
        self.progress_label["text"] = f"{value}/{self.progress_bar['maximum']}"
    
    '''
    Send Data to Manual Review
    '''     
    def send_to_review(self):
        pending_review_dir = self.master.pending_review_dir
        candidate_paths = self.candidate_paths.copy() 
        self.candidate_paths.clear()
        candidate_images = {path: self.master.master_image_dict[path] for path in candidate_paths}
        for image_path, image_data in candidate_images.items():
            dest_path = os.path.join(pending_review_dir, os.path.basename(image_path))
            shutil.copy2(image_path, dest_path)
            image_data['working_directory'] = pending_review_dir
            self.master.master_image_dict[dest_path] = image_data
            del self.master.master_image_dict[image_path]
            os.remove(image_path)
        updated_image_paths = [path for path in self.master.master_image_dict
                               if self.master.master_image_dict[path]['working_directory'] == pending_review_dir 
                               and path not in self.sent_paths]
        self.sent_paths.extend(updated_image_paths)
        self.master.views['Manual'].receive_data(updated_image_paths)
        self.master.change_view('Manual')
        self.clear_gallery()
    '''
    Cancel/pause/resume the processing
    '''   
    def stop_processing(self):
        self.master.views['Upload'].stop_processing()
        self.set_progress_maximum(0)
        self.update_progress(0)
        self.stop_processing_button["state"] = tk.DISABLED

    def pause_processing(self):
        self.master.views['Upload'].pause_processing()
        self.pause_processing_button.config(text="Resume Processing", command=self.resume_processing)
    
    def resume_processing(self):
        self.master.views['Upload'].resume_processing()
        self.pause_processing_button.config(text="Pause Processing", command=self.pause_processing)
       
    '''
    Recieve and display data
    '''   
    def receive_data(self, image_file_path):
        # Check if more images can be loaded
        if self.images_loaded < 100:
            self.load_single_image(image_file_path)
            self.images_loaded += 1

            # Enable 'Load More' button if the initial set of images have been loaded
            if self.images_loaded >= 100:
                self.load_more_button["state"] = tk.NORMAL

    def load_single_image(self, image_path):
        self.candidate_paths.append(image_path)
        # Retrieve image data from the master image dictionary
        image_data = self.master.master_image_dict.get(image_path, {})
        photo_object = image_data.get('photo_object')
        tags = image_data.get('tags', {})

        # Resize the image to display width using the photo object
        resized_image = self.resize_image(photo_object)
        formatted_tags = ", ".join(tags.values()) if tags else ""

        # Add the resized image and tags to the gallery
        self.add_image_to_gallery(resized_image, formatted_tags)

    def resize_image(self, image):
        display_width = self.master.views["Upload"].width_entry.get() 
        display_width = int(display_width)
        original_width, original_height = image.size
        aspect_ratio = original_width / original_height
        new_width = display_width
        new_height = int(new_width / aspect_ratio)
        image = image.resize((new_width, new_height))
        return image

    def add_image_to_gallery(self, image, formatted_tags):
        try:
            photo = ImageTk.PhotoImage(image)
            self.imageTk_objects.append(photo)
            # Calculate image's contribution to row width (including padding)
            image_width_with_padding = photo.width() + 20 
            
            # Check if adding this image would exceed the max frame width
            if self.current_row_width + image_width_with_padding > self.canvas.winfo_width():
                # Reset for new row
                self.current_row_width = 0
                self.current_col = 0
                self.current_row += 1
            
            img_label = ttk.Label(self.frame_images, image=photo)
            img_label.grid(row=self.current_row, column=self.current_col, sticky="nw", padx=5, pady=5)  
            img_label.bind("<MouseWheel>", self._on_mousewheel)
            
            # Add tags as a label to the image
            if formatted_tags:
                tag_label = ttk.Label(self.frame_images, text=formatted_tags, background='#eff0f1', anchor='e')
                tag_label.grid(row=self.current_row, column=self.current_col, sticky="ne", padx=5, pady=5)
                tag_label.bind("<MouseWheel>", self._on_mousewheel)

            self.current_row_width += image_width_with_padding
            self.current_col += 1
        
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

            self.update()
            self.canvas.update_idletasks()

        except Exception as e:
            print(f"Error displaying image: {e}")
      
    def load_more_images(self):
        self.load_more_button["state"] = tk.DISABLED
        load_count = 100 if self.images_loaded >= 100 else 100

        remaining_images = {k: v for k, v in self.image_tag_mappings.items() if k not in self.candidate_images}
        image_paths = list(remaining_images.keys())

        for image_path in image_paths[:load_count]:
            features = remaining_images.get(image_path, {}).get('tags', {})
            if features:
                self.load_single_image(image_path, features)
                self.images_loaded += 1
            self.load_more_button["state"] = tk.NORMAL
    '''
    Clear Images
    '''         
    def clear_gallery(self):
        """Clears all images from the gallery view."""
        for widget in self.frame_images.winfo_children():
            widget.destroy()
        self.imageTk_objects.clear()
        self.image_positions.clear()
        self.row_heights.clear()
        self.current_row_width = 0
        self.current_col = 0
        self.current_row = 0
        self.images_loaded = 0
        self.load_more_button["state"] = tk.DISABLED

