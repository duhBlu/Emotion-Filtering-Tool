import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from io import BytesIO

class GalleryView(ttk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.initialized = True
        self.candidate_images = []
        self.image_tag_mappings = {}
        self.image_positions = []
        self.row_heights = []
        self.current_col = 0 # for keeping track of the image positions
        self.current_row = 0
        self.current_col = 0
        self.current_row = 0
        self.current_row_width = 0 
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
        
        # cancel the processing so user can change the settings without having to wait for the processing to finish
        self.stop_processing_button = ttk.Button(self, text="Stop processing", command=self.stop_processing)
        self.stop_processing_button.grid(row=2, column=0, padx=(5, 20), pady=20, sticky='w')  # Adjusted padx
        
        # clear the gallery so user can start over  without sending the images to manual review
        self.clear_clear_button = ttk.Button(self, text="clear", command=self.clear_gallery)
        self.clear_clear_button.grid(row=2, column=0, padx=(130, 5), pady=20, sticky='w') 
        
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
            self.progress_bar["maximum"] = max_value

    def update_progress(self, value):
        self.progress_var.set(value)
        self.progress_label["text"] = f"{value}/{self.progress_bar['maximum']}"
    
    '''
    Send Data to Manual Review
    '''     
    def send_to_review(self):
        self.master.views['Manual Image Review'].show_images(self.candidate_images)
        self.master.change_view('Manual Image Review')
        self.clear_gallery()
    
    '''
    Cancel the processing
    '''   
    def stop_processing(self):
        self.master.views['Data Upload & Image Selection'].cancellation_requested = True
        self.set_progress_maximum(0)
        self.update_progress(0)

    '''
    Recieve and display data
    '''   
    def receive_data(self, candidate_folder, image_tag_mapping):
        self.candidate_folder = candidate_folder
        # Combine with existing image_tag_mappings if present
        self.image_tag_mappings = {**self.image_tag_mappings, **image_tag_mapping}
        image_path = list(image_tag_mapping.keys())[0] if image_tag_mapping else None
        features = image_tag_mapping.get(image_path, {}).get('tags', {})
        if features:
            self.load_single_image(image_path, features)

    def load_single_image(self, image_path, features=None):
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            image = Image.open(BytesIO(image_data))
            target_width = self.master.views["Data Upload & Image Selection"].width_entry.get()
            resized_image = self.resize_image_to_display_width(image, 200)  
            tags = features if features else self.image_tag_mappings.get(image_path, {}).get('tags', {})
            formatted_tags = ([f"{v} " for _, v in tags.items()])
            self.add_image_to_gallery(resized_image, formatted_tags)
            print(f"Loaded {image_path} with tags: {formatted_tags}")
        except Exception as e:
            print(f"Error loading {image_path}. Reason: {e}")

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
            image_width_with_padding = photo.width() + 10 
            
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

            self.current_row_width += image_width_with_padding
            self.current_col += 1
        
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

            self.update()
            self.canvas.update_idletasks()

        except Exception as e:
            print(f"Error displaying image: {e}")
            
    '''
    Clear Images
    '''         
    def clear_gallery(self):
        """Clears all images from the gallery view."""
        for widget in self.frame_images.winfo_children():
            widget.destroy()

        # Reset attributes to their initial states
        self.candidate_images = []
        self.image_tag_mappings = {}
        self.image_positions = []
        self.row_heights = []
        self.current_row_width = 0
        self.current_col = 0
        self.current_row = 0





        
