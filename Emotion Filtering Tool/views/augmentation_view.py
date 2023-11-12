from re import S
import tkinter as tk
from tkinter import ttk
from collections import defaultdict
from PIL import Image, ImageTk
import tkinter.messagebox as messagebox

class AugmentationView(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.current_row = 0
        self.current_col = 0
        self.pending_export_image_paths = []
        self.imageTk_objects = []
        self.aug_imageTk_objects = []
        self.current_row_width = 0
        self.selected_images = defaultdict(bool)
        self.changed_images = set()
        self.image_labels = {}
        self.original_images = {}
        self.modified_images = {}
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

        self.augment_button = ttk.Button(self, text="Process Selected", command=self.augment_images)
        self.augment_button.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.export_button = ttk.Button(self, text="Export All", command=self.save_augmented_images)
        self.export_button.grid(row=1, column=0, padx=10, pady=10, sticky="e")

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta//120), "units")

    '''
    Send Images to Data Export View
    '''
    def save_augmented_images(self):
        export_data = {}
        for file_path, data in self.photo_images.items():
            export_data[file_path] = data['tags']
        self.master.views['Export'].receive_images(export_data)
        self.clear_images()
        self.master.change_view('Export')
    
    def clear_images(self):
        for widget in self.frame_images.winfo_children():
            widget.destroy()
        self.image_frames.clear()
        self.check_buttons.clear()
        self.photo_images.clear()
        self.selected_images.clear()
        self.current_row = 0
        self.current_col = 0
        self.current_row_width = 0
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    '''
    Load and Display Images
    '''    
    def receive_data(self, image_paths):
        existing_paths_set = set(self.pending_export_image_paths)
        new_paths = [item for item in image_paths if item not in existing_paths_set]
        self.pending_export_image_paths.extend(new_paths)
        self.total_images = len(self.pending_export_image_paths)  # Store the initial total number of images
        self.show_images(new_paths)

    
    def show_images(self, image_paths):
        for idx, image_path in enumerate(image_paths):
            image_data = self.master.master_image_dict.get(image_path, {})
            photo_object = image_data.get('photo_object')
            tags = image_data.get('tags', {})
            
            resized_image = self.resize_image(photo_object)
            formatted_tags = ", ".join(tags.values()) if tags else ""
            
            self.add_image_to_augment(idx, resized_image, formatted_tags)
    
        # Update canvas scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def resize_image(self, image, width=None):
        if width is not None:
            display_width = width
        else:            
            display_width = self.master.views["Upload"].width_entry.get() 
        display_width = int(display_width)
        original_width, original_height = image.size
        aspect_ratio = original_width / original_height
        new_width = display_width
        new_height = int(new_width / aspect_ratio)
        image = image.resize((new_width, new_height))
        return image
    
    def update_image_in_grid(self, image_path, new_image):
        if image_path in self.image_labels:
            resized_image = self.resize_image(new_image)
            photo = ImageTk.PhotoImage(resized_image)
            self.image_labels[image_path].config(image=photo)
            self.image_labels[image_path].image = photo  # Keep the reference
            self.update_idletasks()


    def add_image_to_augment(self, idx, image, tags):
        photo = ImageTk.PhotoImage(image)
        self.imageTk_objects.append(photo)
        
        image_width_with_padding = photo.width() + 10

        if self.current_row_width + image_width_with_padding > self.canvas.winfo_width():
            self.current_row_width = 0
            self.current_col = 0
            self.current_row += 1

        check_var = tk.IntVar()
        img_label = ttk.Label(self.frame_images, image=photo)
        img_label.grid(row=self.current_row, column=self.current_col, sticky="nw", padx=5, pady=5)
        self.image_labels[self.pending_export_image_paths[idx]] = img_label
        img_label.bind("<Button-1>", lambda event, idx=idx, var=check_var: self.image_click(idx, var))
        img_label.bind("<MouseWheel>", self._on_mousewheel)

        checkbutton = ttk.Checkbutton(self.frame_images, variable=check_var)
        checkbutton.grid(row=self.current_row, column=self.current_col, sticky="nw", padx=5, pady=5)
        checkbutton['command'] = lambda idx=idx, var=check_var: self.toggle_selection(idx, var)

        tag_label = ttk.Label(self.frame_images, text=tags)
        tag_label.grid(row=self.current_row, column=self.current_col, sticky="ne", padx=5, pady=5)
        tag_label.bind("<MouseWheel>", self._on_mousewheel)
        
        self.current_row_width += image_width_with_padding
        self.current_col += 1

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    
    '''
    Image Selection logic
    ''' 
    def image_click(self, idx, var):
        # Toggle checkbox state
        var.set(1 - var.get())
        # Update the selection
        self.toggle_selection(idx, var)

    def toggle_selection(self, idx, var):
        self.selected_images[idx] = bool(var.get())          
        
    '''
    Augmentation Window and Logic
    ''' 
    def augment_images(self):
        # Initialize counters and make them instance variables
        self.current_image_idx = 0
        selected_indices = [idx for idx, selected in self.selected_images.items() if selected]
        total_images = len(selected_indices)
        self.selected_indices_queue = selected_indices
        self.selected_image_paths = [self.pending_export_image_paths[idx] for idx in selected_indices]
        self.current_image_path = None
        
        if not self.selected_image_paths:
            messagebox.showinfo("No Images Selected", "Please select at least one image to process.")
            return 
        
        self.augment_window = tk.Toplevel(self)
        self.augment_window.title("Augmentation")
        
        # Set column weights (relative widths)
        # Set column and row weights for augment_window
        self.augment_window.grid_columnconfigure(0, weight=1)
        self.augment_window.grid_columnconfigure(1, weight=3)  # Give image frame more space
        self.augment_window.grid_rowconfigure(0, weight=1)
    
        option_frame = ttk.Frame(self.augment_window)
        option_frame.grid(row=0, column=0, sticky="nsew")
    
        # Set column and row weights for option_frame
        option_frame.grid_columnconfigure(0, weight=1)
        option_frame.grid_rowconfigure((0, 1), weight=1)

        option_label = ttk.Label(option_frame, text="Add augmentation options here")
        option_label.grid(row=0, column=0, sticky="n", pady=10)  
    
        change_button = ttk.Button(option_frame, text="Mark as Changed", command=self.aug_flip)
        change_button.grid(row=1, column=0, pady=5)  

        image_frame = ttk.Frame(self.augment_window)
        image_frame.grid(row=0, column=1, sticky="nsew")
    
        # Set column and row weights for image_frame
        image_frame.grid_columnconfigure((0, 1, 2), weight=1)  # Allow all columns to expand
        image_frame.grid_rowconfigure(0, weight=1)  # Allow image row to expand
    
        self.img_label = ttk.Label(image_frame)
        self.img_label.grid(row=0, column=1, columnspan=3, sticky="") 


        button_frame = ttk.Frame(image_frame)
        button_frame.grid(row=1, column=1, columnspan=3, sticky="", pady=5)   
    
        # Label to display "image x of x"
        label_text = tk.StringVar()
        progress_label = ttk.Label(button_frame, textvariable=label_text)
        progress_label.grid(row=1, column=1)
        label_text.set(f"Image {self.current_image_idx + 1} of {total_images}")

        reject_button = ttk.Button(button_frame, text="Cancel", command=lambda: self.cancel_augment())
        reject_button.grid(row=1, column=0, padx=(0, 5))
        
        accept_button = ttk.Button(button_frame, text="Accept", command=lambda: self.accept_augment())
        accept_button.grid(row=1, column=2, padx=5)

        self.label_text = label_text
        self.reject_button = reject_button
        self.accept_button = accept_button
        
        self.current_image_path = self.selected_image_paths[self.current_image_idx]
        self.show_next_image(False)

        self.update_buttons()
    
    # Sample augmentation function
    def aug_flip(self):
        if self.current_image_path:
            # Check if the image has already been modified
            if self.current_image_path in self.modified_images:
                # If it has been modified, get the modified version
                pil_image = self.modified_images[self.current_image_path]
            else:
                # If it hasn't been modified, get the original
                pil_image = self.master.master_image_dict[self.current_image_path]['photo_object']

            # Perform the flip operation
            flipped_image = pil_image.transpose(Image.FLIP_LEFT_RIGHT)
            flipped_image = self.resize_image(flipped_image)
            # Update the temporary storage with the flipped image
            self.modified_images[self.current_image_path] = flipped_image
            
            # Create a new PhotoImage and update the label
            tk_flipped_image = ImageTk.PhotoImage(flipped_image)
            self.img_label.config(image=tk_flipped_image)
            self.img_label.image = tk_flipped_image  # Store a reference to the new PhotoImage

            # Indicate that the current image has been modified
            self.changed_images.add(self.current_image_path)
            self.update_buttons()

            
    def update_buttons(self):
        # Use self.current_image_path to check if the image has been changed
        if self.current_image_path in self.changed_images:
            self.reject_button['state'] = tk.NORMAL
            self.accept_button['text'] = "Accept"
            self.accept_button['command'] = self.accept_changes  # You may remove the lambda if not passing arguments
        else:
            self.reject_button['state'] = tk.DISABLED
            self.accept_button['text'] = "Skip" 
            self.accept_button['command'] = self.skip_image  # Same here, no need for lambda

            
    def update_ui_after_change(self):
        # Update buttons state
        self.update_buttons()

        # Update label text to show current image index out of the total number of images
        current_idx = self.selected_image_paths.index(self.current_image_path) if self.current_image_path in self.selected_image_paths else 0
        self.label_text.set(f"Image {current_idx + 1} of {self.total_images}")

        
    def accept_changes(self):
        if self.current_image_path in self.modified_images:
            # Save the modified image to the master_image_dict
            modified_image = self.modified_images[self.current_image_path]
            self.master.master_image_dict[self.current_image_path]['photo_object'] = modified_image
            # Update the image in the grid
            self.update_image_in_grid(self.current_image_path, modified_image)

            # Remove the path from modified images since changes are accepted
            del self.modified_images[self.current_image_path]
            self.changed_images.discard(self.current_image_path)

            # Move to the next image and update the UI
            self.show_next_image(increment=True, accepted=True)
            self.update_ui_after_change()


    def skip_image(self):     
        self.show_next_image()
           
    def cancel_augment(self):
        if self.current_image_path:
            # Remove the modified image from the temporary storage
            self.modified_images.pop(self.current_image_path, None)

            # Revert the image label to display the original image
            original_image = self.master.master_image_dict[self.current_image_path]['photo_object']
            tk_original_image = ImageTk.PhotoImage(self.resize_image(original_image))
            self.img_label.config(image=tk_original_image)
            self.img_label.image = tk_original_image  # Store a reference to the original PhotoImage

            # Indicate that the current image has been reverted
            self.changed_images.discard(self.current_image_path)
            self.update_buttons()


    def show_next_image(self, increment=True, accepted=False):
        # If the current image was accepted, remove it from the list of paths
        if accepted and self.current_image_path in self.selected_image_paths:
            self.selected_image_paths.remove(self.current_image_path)
            self.changed_images.discard(self.current_image_path)  # Also remove from changed images

        # Determine the next image to display
        if increment and self.selected_image_paths:
            current_idx = self.selected_image_paths.index(self.current_image_path) if self.current_image_path in self.selected_image_paths else -1
            next_idx = current_idx + 1 if current_idx + 1 < len(self.selected_image_paths) else 0

            # Update current_image_path to the next image path if available
            if next_idx < len(self.selected_image_paths):
                self.current_image_path = self.selected_image_paths[next_idx]
            else:
                self.current_image_path = None  # No more images to display
                self.augment_window.destroy()  # Close the window if we're done
                return  # Exit the function

        # If there's a next image, display it
        if self.current_image_path:
            image_data = self.master.master_image_dict.get(self.current_image_path)
            pil_image = image_data.get('photo_object')
            pil_image = self.resize_image(pil_image)
            tk_image = ImageTk.PhotoImage(pil_image)

            self.img_label.config(image=tk_image)
            self.img_label.image = tk_image  # Keep a reference

            

