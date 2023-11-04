import tkinter as tk
from tkinter import ttk
from collections import defaultdict
from PIL import ImageTk
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
        self.current_row_width = 0
        self.photo_images = {}
        self.selected_images = defaultdict(bool)
        self.image_frames = {}
        self.index_to_key_mapping = {}
        self.changed_images = set()
        self.original_images = {} 
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
        self.export_button.grid(row=1, column=1, padx=10, pady=10, sticky="e")

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta//120), "units")

    '''
    Send Images to Data Export View
    '''
    def save_augmented_images(self):
        self.master.views['Dataset Export Options'].receive_images(self.photo_images)
        self.clear_images()
        self.master.change_view('Dataset Export Options')
    
    def clear_images(self):
        for frame in self.image_frames.values():
            frame.destroy()
        self.image_frames.clear()
        self.photo_images.clear()
        self.current_row = 0
        self.current_col = 0
        self.current_row_width = 0
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    '''
    Load and Display Images
    '''    
    def load_accepted_images(self, accepted_images):
        self.photo_images.update(accepted_images)
        self.show_images(self.photo_images)    

    def show_images(self, accepted_images):
        for idx, (file_path, image_data) in enumerate(accepted_images.items()):
            photo = image_data['photo']  # Use the photo directly, assuming it's already a PhotoImage
            tags = image_data['tags']
            self.index_to_key_mapping[idx] = file_path
            self.add_image_to_augment(file_path, photo, tags, idx)
    
        # Update canvas scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def add_image_to_augment(self, file_path, photo, tags, idx):
        # The structure and logic here are adjusted to match the Manual Review's method
        image_width_with_padding = photo.width() + 10

        if self.current_row_width + image_width_with_padding > self.canvas.winfo_width():
            self.current_row_width = 0
            self.current_col = 0
            self.current_row += 1

        check_var = tk.IntVar()
        img_label = ttk.Label(self.frame_images, image=photo)
        img_label.grid(row=self.current_row, column=self.current_col, sticky="nw", padx=5, pady=5)
        img_label.bind("<Button-1>", lambda event, idx=idx, var=check_var: self.image_click(idx, var))
        img_label.bind("<MouseWheel>", self._on_mousewheel)

        checkbutton = ttk.Checkbutton(self.frame_images, variable=check_var)
        checkbutton.grid(row=self.current_row, column=self.current_col, sticky="nw", padx=5, pady=5)
        checkbutton['command'] = lambda idx=idx, var=check_var: self.toggle_selection(idx, var)

        tag_string = ', '.join([f"{v}" for _, v in tags.items()])
        tag_label = ttk.Label(self.frame_images, text=tag_string)
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
        self.current_image = 0
        selected_indices = [idx for idx, selected in self.selected_images.items() if selected]
        self.total_images = len(selected_indices)
        self.selected_indices_queue = selected_indices
        
        if self.total_images == 0:
            messagebox.showinfo("No Images Selected", "Please select at least one image to process.")
            return 
        
        augment_window = tk.Toplevel(self)
        augment_window.title("Augmentation")
        
        # Set column weights (relative widths)
        # Set column and row weights for augment_window
        augment_window.grid_columnconfigure(0, weight=1)
        augment_window.grid_columnconfigure(1, weight=3)  # Give image frame more space
        augment_window.grid_rowconfigure(0, weight=1)
    
        option_frame = ttk.Frame(augment_window)
        option_frame.grid(row=0, column=0, sticky="nsew")
    
        # Set column and row weights for option_frame
        option_frame.grid_columnconfigure(0, weight=1)
        option_frame.grid_rowconfigure((0, 1), weight=1)

        option_label = ttk.Label(option_frame, text="Add augmentation options here")
        option_label.grid(row=0, column=0, sticky="n", pady=10)  
    
        change_button = ttk.Button(option_frame, text="Mark as Changed", command=self.mark_as_changed)
        change_button.grid(row=1, column=0, pady=5)  

        image_frame = ttk.Frame(augment_window)
        image_frame.grid(row=0, column=1, sticky="nsew")
    
        # Set column and row weights for image_frame
        image_frame.grid_columnconfigure((0, 1, 2), weight=1)  # Allow all columns to expand
        image_frame.grid_rowconfigure(0, weight=1)  # Allow image row to expand
    
        img_label = ttk.Label(image_frame)
        img_label.grid(row=0, column=1, columnspan=3, sticky="") 


        button_frame = ttk.Frame(image_frame)
        button_frame.grid(row=1, column=1, columnspan=3, sticky="", pady=5)   
    
        # Label to display "image x of x"
        label_text = tk.StringVar()
        progress_label = ttk.Label(button_frame, textvariable=label_text)
        progress_label.grid(row=1, column=1)
        label_text.set(f"Image {self.current_image + 1} of {self.total_images}")

        reject_button = ttk.Button(button_frame, text="Cancel", command=lambda: self.cancel_augment(img_label, augment_window, label_text))
        reject_button.grid(row=1, column=0, padx=(0, 5))
        
        accept_button = ttk.Button(button_frame, text="Accept", command=lambda: self.accept_augment(img_label, augment_window, label_text))
        accept_button.grid(row=1, column=2, padx=5)

        self.reject_button = reject_button
        self.accept_button = accept_button
        
        if self.selected_indices_queue:
            first_idx = self.selected_indices_queue[0]  # Changed from pop(0) to just access
            self.current_image = first_idx  # Use the first index as the current image
            self.show_next_image(first_idx, img_label, augment_window)

        self.update_buttons()
            
    def mark_as_changed(self):
            # Mark the current image as changed
            self.changed_images.add(self.current_image)
            # Update the button texts and states
            self.update_buttons()
            
    def update_buttons(self):
        # No arguments are needed as we saved button references as instance variables
        if self.current_image in self.changed_images:
            self.reject_button['state'] = tk.NORMAL
            self.accept_button['text'] = "Accept"
        else:
            self.reject_button['state'] = tk.DISABLED
            self.accept_button['text'] = "Skip" 
            
    def accept_augment(self, img_label, augment_window, label_text):
        if self.selected_indices_queue:
            current_idx = self.selected_indices_queue.pop(0)
            self.current_image = current_idx  # Update current_image to the current index
            label_text.set(f"Image {self.current_image + 1} of {self.total_images}")

            # If changes have been applied, save and display the augmented image
            if current_idx in self.changed_images:
                original_image_pil = self.original_images[current_idx]
                augmented_image_pil = self.augment_images(original_image_pil)
                augmented_image = ImageTk.PhotoImage(image=augmented_image_pil)
                self.photo_images[current_idx] = augmented_image  # Save augmented image
                img_label.config(image=augmented_image)
                img_label.image = augmented_image
                self.changed_images.remove(current_idx)  # Remove from changed images list
            # If no changes have been applied, simply display the next image
            else:
                if self.selected_indices_queue:
                    next_idx = self.selected_indices_queue[0]
                    next_image_pil = self.original_images[next_idx]
                    next_image = ImageTk.PhotoImage(image=next_image_pil)
                    img_label.config(image=next_image)
                    img_label.image = next_image
                    self.current_image = next_idx

            self.update_buttons()  # Update buttons state
            label_text.set(f"Image {self.current_image + 1} of {self.total_images}")
        else:
            augment_window.destroy()

    def cancel_augment(self, img_label, augment_window, label_text):
        if self.selected_indices_queue:
            current_idx = self.selected_indices_queue[0]
            original_image_pil = self.original_images[current_idx]
            original_image = ImageTk.PhotoImage(image=original_image_pil)
            img_label.config(image=original_image)
            img_label.image = original_image
            if current_idx in self.changed_images:
                self.changed_images.remove(current_idx)  # Revert changes
            self.update_buttons()  # Update the buttons to reflect the reversion
        else:
            augment_window.destroy()

    def show_next_image(self, idx, img_label, augment_window):
        # Get the image path from the index
        image_path = self.index_to_key_mapping.get(idx)

        # Check if the image path exists in the mapping
        if image_path and image_path in self.photo_images:
            self.current_image = idx  # Update the current image index
            tk_image = self.photo_images[image_path]  # Retrieve the image using the path

            img_label.config(image=tk_image['photo'])
            img_label.image = tk_image  # Keep a reference to avoid garbage collection

            self.update_buttons()
        else:
            # Handle the case where the image path is not found
            print(f"No image found for index: {idx}")
